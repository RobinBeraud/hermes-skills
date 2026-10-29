#!/usr/bin/env python3
"""regwatch.py - weekly watch on housing regulation news and mortgage rates.

Reads public RSS feeds, keeps the items that match housing/credit keywords,
de-duplicates them against a state file, and prints a Markdown digest with a
source link on every line. It can also fetch the French new-business mortgage
cost of borrowing from the ECB open data API (no key needed).

Standard library only. Not legal or tax advice.
"""
import argparse
import csv
import io
import json
import os
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (compatible; regwatch/1.0)"

# Feeds checked to answer HTTP 200 with RSS XML when this skill was written.
DEFAULT_FEEDS = {
    "economie.gouv.fr": "https://www.economie.gouv.fr/rss/toutesactualites",
    "ecologie.gouv.fr": "https://www.ecologie.gouv.fr/rss-actualites.xml",
    "ECB press": "https://www.ecb.europa.eu/rss/press.html",
}

DEFAULT_KEYWORDS = [
    "immobilier", "logement", "loyer", "bail", "locatif", "locataire",
    "copropriete", "dpe", "diagnostic de performance",
    "renovation energetique", "maprimerenov", "passoire", "taxe fonciere",
    "plus-value immobiliere", "pret immobilier", "credit immobilier",
    "pret a taux zero", "ptz", "taux d'interet", "taux d'usure",
    "hypothec", "notaire", "dmto", "urbanisme", "permis de construire",
    "mortgage", "housing", "real estate", "residential", "interest rate",
    "interest rates", "bank lending survey", "lending standards",
]

# ECB MIR series: France, new business, households, house purchase,
# annualised agreed rate (all maturities).
ECB_MIR_URL = (
    "https://data-api.ecb.europa.eu/service/data/MIR/"
    "M.FR.B.A2C.AM.R.A.2250.EUR.N?lastNObservations={n}&format=csvdata"
)

DISCLAIMER = (
    "Information watch only. This is not legal, tax or financial advice. "
    "Open each source before acting on it."
)


def norm(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().replace("\u2019", "'")


def fetch(url, timeout=25, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_date(raw):
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml_bytes):
    """Return a list of dicts: title, link, summary, date (RSS 2.0, RDF, Atom)."""
    root = ET.fromstring(xml_bytes)
    items = []
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        d = {"title": "", "link": "", "summary": "", "date": None}
        for ch in el:
            name = local(ch.tag)
            if name == "title":
                d["title"] = (ch.text or "").strip()
            elif name == "link":
                d["link"] = (ch.get("href") or ch.text or "").strip()
            elif name in ("description", "summary") and not d["summary"]:
                d["summary"] = (ch.text or "").strip()
            elif name in ("pubDate", "date", "published", "updated") and not d["date"]:
                d["date"] = parse_date(ch.text)
        if d["title"] and d["link"]:
            items.append(d)
    return items


def matches(item, keywords):
    hay = norm(item["title"] + " " + item["summary"])
    return sorted({k for k in keywords if norm(k) in hay})


def load_state(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return set(json.load(fh).get("seen", []))
    return set()


def save_state(path, seen):
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"seen": sorted(seen)}, fh, indent=1)


def parse_mir_csv(raw):
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        try:
            rows.append((r["TIME_PERIOD"], float(r["OBS_VALUE"])))
        except (KeyError, ValueError):
            continue
    return sorted(rows)


def rate_section(rows):
    if not rows:
        return "## Mortgage cost of borrowing (France)\n- No data returned.\n"
    out = ["## Mortgage cost of borrowing (France, ECB statistics)"]
    for i, (period, val) in enumerate(rows):
        delta = "" if i == 0 else " ({:+.2f} pt vs previous month)".format(val - rows[i - 1][1])
        out.append("- {}: {:.2f} %{}".format(period, val, delta))
    out.append("- Series: ECB MIR, new business, households, house purchase, "
               "annualised agreed rate. Source: https://data.ecb.europa.eu")
    out.append("- This is an average of loans granted, not a quote for your file.")
    return "\n".join(out) + "\n"


def build_digest(items_by_source, rates_rows, days, now):
    lines = ["# Housing regulation and rates watch",
             "Generated {} UTC, window: last {} days.".format(now.strftime("%Y-%m-%d %H:%M"), days), ""]
    if rates_rows is not None:
        lines.append(rate_section(rates_rows))
    total = 0
    for source, items in items_by_source.items():
        lines.append("## " + source)
        if not items:
            lines.append("- Nothing new matching your keywords.")
        for it, kws in items:
            total += 1
            date = it["date"].strftime("%Y-%m-%d") if it["date"] else "n/a"
            lines.append("- {} | {} | keywords: {} | {}".format(
                date, it["title"], ", ".join(kws), it["link"]))
        lines.append("")
    lines.append("Items: {}. {}".format(total, DISCLAIMER))
    return "\n".join(lines)


def collect(feeds, keywords, days, seen, now, loader=fetch):
    cutoff = now - timedelta(days=days)
    result, errors, new_seen = {}, [], set(seen)
    for name, url in feeds.items():
        try:
            items = parse_feed(loader(url))
        except Exception as exc:  # network or XML problems must not stop the run
            errors.append("{}: {}".format(name, exc))
            result[name] = []
            continue
        kept = []
        for it in items:
            if it["link"] in seen:
                continue
            if it["date"] and it["date"] < cutoff:
                continue
            kws = matches(it, keywords)
            if kws:
                kept.append((it, kws))
                new_seen.add(it["link"])
        kept.sort(key=lambda p: p[0]["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        result[name] = kept
    return result, errors, new_seen


SAMPLE_RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Nouvelle aide \xc3\xa0 la r\xc3\xa9novation \xc3\xa9nerg\xc3\xa9tique du logement</title>
<link>https://example.com/a</link><description>MaPrimeR\xc3\xa9nov et DPE</description>
<pubDate>Tue, 27 Oct 2026 10:00:00 +0100</pubDate></item>
<item><title>Recette de cuisine</title><link>https://example.com/b</link>
<description>Rien \xc3\xa0 voir</description><pubDate>Tue, 27 Oct 2026 09:00:00 +0100</pubDate></item>
<item><title>Ancien article sur le loyer</title><link>https://example.com/c</link>
<description>loyer</description><pubDate>Mon, 01 Jan 2024 09:00:00 +0100</pubDate></item>
<item><title>Euro area bank lending survey: mortgage demand</title><link>https://example.com/d</link>
<description></description><pubDate>2026-10-26 08:00:00</pubDate></item>
</channel></rss>"""

SAMPLE_CSV = ("KEY,TIME_PERIOD,OBS_VALUE\nk,2026-06,3.16\nk,2026-07,3.18\nk,2026-08,3.20\n")


def selftest():
    now = datetime(2026, 10, 29, tzinfo=timezone.utc)
    feeds = {"sample": "mem://sample"}
    res, errs, seen = collect(feeds, DEFAULT_KEYWORDS, 14, set(), now, loader=lambda u: SAMPLE_RSS)
    links = [it["link"] for it, _ in res["sample"]]
    assert links == ["https://example.com/a", "https://example.com/d"], links
    assert not errs
    # second run with state: everything already seen
    res2, _, _ = collect(feeds, DEFAULT_KEYWORDS, 14, seen, now, loader=lambda u: SAMPLE_RSS)
    assert res2["sample"] == []
    # a failing feed is reported, not fatal
    def boom(u):
        raise OSError("offline")
    res3, errs3, _ = collect(feeds, DEFAULT_KEYWORDS, 14, set(), now, loader=boom)
    assert errs3 and res3["sample"] == []
    rows = parse_mir_csv(SAMPLE_CSV)
    assert rows[-1] == ("2026-08", 3.2)
    text = build_digest(res, rows, 14, now)
    assert "+0.02 pt" in text and "https://example.com/a" in text
    print(text)
    print("\nSELFTEST OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=7, help="look-back window (default 7)")
    ap.add_argument("--feed", action="append", default=[], metavar="NAME=URL",
                    help="add a feed (repeatable)")
    ap.add_argument("--only-custom", action="store_true", help="ignore the built-in feeds")
    ap.add_argument("--keyword", action="append", default=[], help="add a keyword (repeatable)")
    ap.add_argument("--state", help="JSON file used to hide items already reported")
    ap.add_argument("--rates", type=int, default=0, metavar="N",
                    help="append the last N monthly ECB mortgage rates for France")
    ap.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    ap.add_argument("--selftest", action="store_true", help="offline self-test")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0

    feeds = {} if a.only_custom else dict(DEFAULT_FEEDS)
    for spec in a.feed:
        if "=" not in spec:
            ap.error("--feed expects NAME=URL")
        k, v = spec.split("=", 1)
        feeds[k] = v
    keywords = DEFAULT_KEYWORDS + a.keyword
    now = datetime.now(timezone.utc)
    seen = load_state(a.state)
    result, errors, new_seen = collect(feeds, keywords, a.days, seen, now)

    rows = None
    if a.rates:
        try:
            rows = parse_mir_csv(fetch(ECB_MIR_URL.format(n=a.rates), accept="text/csv").decode("utf-8"))
        except Exception as exc:
            errors.append("ECB rates: {}".format(exc))
            rows = []

    if a.json:
        print(json.dumps({
            "generated": now.isoformat(),
            "rates": rows,
            "items": {s: [{"title": i["title"], "link": i["link"],
                           "date": i["date"].isoformat() if i["date"] else None,
                           "keywords": k} for i, k in v] for s, v in result.items()},
            "errors": errors}, ensure_ascii=False, indent=1))
    else:
        print(build_digest(result, rows, a.days, now))
    for e in errors:
        print("WARNING: " + e, file=sys.stderr)
    save_state(a.state, new_seen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
