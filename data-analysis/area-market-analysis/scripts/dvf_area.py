#!/usr/bin/env python3
"""Local property market snapshot for a French commune from open DVF data.

Source: "Demandes de valeurs foncieres geolocalisees" (geo-dvf), published on
data.gouv.fr. No API key. Python 3 standard library only.

Usage:
  dvf_area.py --commune Bordeaux --years 2021-2024
  dvf_area.py --insee 33063 --years 2022,2023 --json
  dvf_area.py --file local.csv --label "My sample"
  dvf_area.py --selftest
"""
import argparse
import csv
import io
import json
import os
import statistics
import sys
import urllib.parse
import urllib.request
from collections import defaultdict

BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"
GEO = "https://geo.api.gouv.fr/communes"
CACHE = os.environ.get("DVF_CACHE", "/tmp/dvf_cache")
UA = {"User-Agent": "hermes-skill-area-market-analysis/1.0"}

# Cities whose DVF files are split by arrondissement.
SPLIT = {
    "75056": ["751%02d" % i for i in range(1, 21)],
    "69123": ["6938%d" % i for i in range(1, 10)],
    "13055": ["132%02d" % i for i in range(1, 17)],
}


def http_get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def resolve_commune(name):
    url = GEO + "?" + urllib.parse.urlencode(
        {"nom": name, "fields": "nom,code,codesPostaux,population", "limit": 5, "boost": "population"})
    data = json.loads(http_get(url, 30))
    if not data:
        raise SystemExit("No commune found for %r" % name)
    return data[0]["code"], data[0]["nom"], data


def fetch_year(insee, year):
    """Return CSV text for one commune/year (cached). Empty string if no file."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "%s_%s.csv" % (insee, year))
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    dep = insee[:3] if insee.startswith("97") else insee[:2]
    url = "%s/%s/communes/%s/%s.csv" % (BASE, year, dep, insee)
    try:
        text = http_get(url).decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""
        raise
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def analyse(csv_text, min_ppm2, max_ppm2):
    """Group rows by mutation and classify. Returns dict of stats for one dataset."""
    muts = defaultdict(list)
    for row in csv.DictReader(io.StringIO(csv_text)):
        if row.get("nature_mutation") != "Vente":
            continue
        muts[row["id_mutation"]].append(row)

    cats = defaultdict(int)
    prices = {"Appartement": [], "Maison": []}
    values = {"Appartement": [], "Maison": []}
    surfaces = {"Appartement": [], "Maison": []}
    rooms_ppm2 = defaultdict(list)
    excluded_outliers = 0

    for mid, rows in muts.items():
        locals_ = {}
        for r in rows:
            t = r.get("type_local", "")
            if t in ("Appartement", "Maison", "Local industriel. commercial ou assimilé"):
                key = (t, r.get("surface_reelle_bati"), r.get("nombre_pieces_principales"),
                       r.get("lot1_numero"))
                locals_[key] = r
        habs = [k for k in locals_ if k[0] in ("Appartement", "Maison")]
        commercial = [k for k in locals_ if k[0].startswith("Local")]
        if commercial:
            cats["commercial_or_mixed"] += 1
            continue
        if len(habs) == 0:
            cats["land_or_other"] += 1
            continue
        if len(habs) > 1:
            cats["multi_unit"] += 1
            continue
        key = habs[0]
        r = locals_[key]
        kind = key[0]
        value = num(r.get("valeur_fonciere"))
        surf = num(r.get("surface_reelle_bati"))
        cats["single_" + ("apartment" if kind == "Appartement" else "house")] += 1
        if not value or not surf or surf <= 0:
            continue
        ppm2 = value / surf
        if not (min_ppm2 <= ppm2 <= max_ppm2):
            excluded_outliers += 1
            continue
        prices[kind].append(ppm2)
        values[kind].append(value)
        surfaces[kind].append(surf)
        if kind == "Appartement":
            p = num(r.get("nombre_pieces_principales"))
            if p is not None:
                rooms_ppm2[min(int(p), 5)].append(ppm2)

    def summ(kind):
        p = prices[kind]
        if not p:
            return {"n": 0}
        q = statistics.quantiles(p, n=4) if len(p) >= 4 else [min(p), statistics.median(p), max(p)]
        return {
            "n": len(p),
            "median_eur_m2": round(statistics.median(p)),
            "q1_eur_m2": round(q[0]),
            "q3_eur_m2": round(q[-1]),
            "median_price_eur": round(statistics.median(values[kind])),
            "median_surface_m2": round(statistics.median(surfaces[kind]), 1),
        }

    return {
        "sales_total": len(muts),
        "categories": dict(cats),
        "apartments": summ("Appartement"),
        "houses": summ("Maison"),
        "apartment_by_rooms": {
            str(k): {"n": len(v), "median_eur_m2": round(statistics.median(v))}
            for k, v in sorted(rooms_ppm2.items())},
        "outliers_excluded": excluded_outliers,
    }


def parse_years(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def pct(a, b):
    if not a or not b:
        return None
    return round((b - a) / a * 100, 1)


def render(label, result):
    years = sorted(result)
    lines = ["Area: %s" % label,
             "Source: DVF geolocated (data.gouv.fr), sales ('Vente') only, outliers filtered",
             ""]
    lines.append("%-6s %7s | %-34s | %-34s" % ("Year", "Sales", "Apartments (n / median EUR/m2 / IQR)", "Houses (n / median EUR/m2 / IQR)"))
    for y in years:
        d = result[y]
        def f(s):
            if not s["n"]:
                return "-"
            return "%d / %d / %d-%d" % (s["n"], s["median_eur_m2"], s["q1_eur_m2"], s["q3_eur_m2"])
        lines.append("%-6s %7d | %-34s | %-34s" % (y, d["sales_total"], f(d["apartments"]), f(d["houses"])))
    if len(years) >= 2:
        a, b = result[years[0]], result[years[-1]]
        lines.append("")
        lines.append("Change %s -> %s (median EUR/m2, indicative, mix effects not removed):" % (years[0], years[-1]))
        for k, name in (("apartments", "Apartments"), ("houses", "Houses")):
            c = pct(a[k].get("median_eur_m2"), b[k].get("median_eur_m2"))
            lines.append("  %s: %s" % (name, ("%+.1f%%" % c) if c is not None else "n/a"))
        c = pct(a["sales_total"], b["sales_total"])
        lines.append("  Sales volume: %s" % (("%+.1f%%" % c) if c is not None else "n/a"))
    last = result[years[-1]]
    lines.append("")
    lines.append("Latest year (%s) sales by category: %s" % (years[-1], json.dumps(last["categories"], sort_keys=True)))
    if last["apartment_by_rooms"]:
        lines.append("Apartments by rooms (5 = 5+): " + ", ".join(
            "%s: n=%d, %d EUR/m2" % (k, v["n"], v["median_eur_m2"]) for k, v in last["apartment_by_rooms"].items()))
    small = [y for y in years if 0 < result[y]["apartments"]["n"] < 30 or 0 < result[y]["houses"]["n"] < 30]
    if small:
        lines.append("Warning: fewer than 30 observations in some segments for %s; medians are fragile." % ", ".join(map(str, small)))
    return "\n".join(lines)


SELFTEST_CSV = """id_mutation,nature_mutation,valeur_fonciere,type_local,surface_reelle_bati,nombre_pieces_principales,lot1_numero
A1,Vente,200000,Appartement,50,2,1
A1,Vente,200000,Appartement,50,2,1
A2,Vente,300000,Appartement,60,3,4
A3,Vente,100000,Appartement,40,2,5
A3,Vente,100000,Appartement,30,1,6
H1,Vente,400000,Maison,100,5,
H1,Vente,400000,,,,
L1,Vente,50000,,,,
C1,Vente,500000,Local industriel. commercial ou assimilé,200,0,
E1,Echange,100000,Appartement,50,2,
X1,Vente,1000,Appartement,50,2,9
"""


def selftest():
    r = analyse(SELFTEST_CSV, 500, 30000)
    assert r["sales_total"] == 7, r
    assert r["apartments"]["n"] == 2, r
    assert r["apartments"]["median_eur_m2"] == 4500, r  # 4000 and 5000
    assert r["houses"]["median_eur_m2"] == 4000, r
    assert r["categories"]["multi_unit"] == 1, r
    assert r["categories"]["land_or_other"] == 1, r
    assert r["categories"]["commercial_or_mixed"] == 1, r
    assert r["outliers_excluded"] == 1, r
    assert parse_years("2021-2023,2025") == [2021, 2022, 2023, 2025]
    assert pct(100, 110) == 10.0
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commune", help="Commune name (resolved via geo.api.gouv.fr)")
    ap.add_argument("--insee", help="INSEE commune code (e.g. 33063)")
    ap.add_argument("--years", default="2021-2024", help="e.g. 2021-2024 or 2022,2024 (available: 2021-2025)")
    ap.add_argument("--file", help="Analyse a local DVF CSV instead of downloading")
    ap.add_argument("--label", help="Label for --file output")
    ap.add_argument("--min-ppm2", type=float, default=500, help="Drop sales below this EUR/m2 (default 500)")
    ap.add_argument("--max-ppm2", type=float, default=30000, help="Drop sales above this EUR/m2 (default 30000)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    result = {}
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            result[0] = analyse(f.read(), a.min_ppm2, a.max_ppm2)
        label = a.label or a.file
    else:
        if a.insee:
            insee, label = a.insee, "INSEE " + a.insee
        elif a.commune:
            insee, label, cands = resolve_commune(a.commune)
            if len(cands) > 1:
                print("Note: %d matches, using %s (%s). Others: %s" % (
                    len(cands), label, insee, ", ".join("%s(%s)" % (c["nom"], c["code"]) for c in cands[1:])), file=sys.stderr)
            label = "%s (%s)" % (label, insee)
        else:
            ap.error("give --commune, --insee or --file")
        codes = SPLIT.get(insee, [insee])
        for y in parse_years(a.years):
            text = ""
            for c in codes:
                part = fetch_year(c, y)
                if part:
                    # keep a single header when concatenating arrondissements
                    text = part if not text else text + part.split("\n", 1)[1]
            if not text:
                print("No data for %s in %s (skipped)" % (insee, y), file=sys.stderr)
                continue
            result[y] = analyse(text, a.min_ppm2, a.max_ppm2)
    if not result:
        raise SystemExit("No data retrieved.")
    if a.json:
        print(json.dumps({"area": label, "source": "geo-dvf (data.gouv.fr)", "years": result}, indent=2, ensure_ascii=False))
    else:
        print(render(label, result))


if __name__ == "__main__":
    main()
