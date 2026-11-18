#!/usr/bin/env python3
"""Summarise a creator analytics CSV export (standard library only).

Usage:
  digest.py export.csv [--metric COLUMN] [--title COLUMN] [--date COLUMN] [--top N]
  digest.py --selftest
Works with exports from YouTube Studio, Instagram, TikTok, LinkedIn or any
spreadsheet that has one row per post/video. Column names are auto-detected
but can be forced with the options above.
"""
import argparse, csv, io, re, statistics, sys, tempfile, os
from datetime import datetime

METRIC_HINTS = ["views", "impressions", "reach", "plays", "watch time", "engagement",
                "likes", "clicks", "shares", "saves", "comments", "subscribers",
                "vues", "vistas", "impressions", "j'aime", "me gusta"]
TITLE_HINTS = ["title", "video title", "caption", "post", "content", "name", "description", "titre", "titulo", "légende", "legende"]
DATE_HINTS = ["publish", "date", "time", "posted", "created", "publi", "fecha"]
DATE_FORMATS = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%m/%d/%Y",
                "%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%Y/%m/%d", "%d.%m.%Y"]


def to_number(s):
    """Parse '1,234', '1 234', '12.5%', '2.3K', '1.2M'. Returns None if not numeric."""
    if s is None:
        return None
    t = str(s).strip().replace("\u202f", "").replace("\xa0", "")
    if not t or t in {"-", "--", "N/A", "n/a"}:
        return None
    mult = 1
    if t[-1:] in "kKmM" and len(t) > 1:
        mult = 1000 if t[-1] in "kK" else 1000000
        t = t[:-1]
    t = t.rstrip("%").replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")
    elif re.fullmatch(r"-?\d+,\d+", t):
        t = t.replace(",", ".")
    try:
        return float(t) * mult
    except ValueError:
        return None


def to_date(s):
    t = (s or "").strip()
    if not t:
        return None
    for f in DATE_FORMATS:
        try:
            return datetime.strptime(t, f)
        except ValueError:
            pass
    return None


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        text = fh.read()
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def pick(cols, hints, forced=None, exclude=()):
    if forced:
        for c in cols:
            if c.strip().lower() == forced.strip().lower():
                return c
        raise SystemExit("Column not found: %r. Available: %s" % (forced, ", ".join(cols)))
    for h in hints:
        for c in cols:
            if c not in exclude and h in c.lower():
                return c
    return None


def analyse(rows, metric=None, title=None, date=None, top=3):
    if not rows:
        raise SystemExit("The file has no data rows.")
    cols = list(rows[0].keys())
    date_c = pick(cols, DATE_HINTS, date)
    title_c = pick(cols, TITLE_HINTS, title, exclude=(date_c,))
    if metric:
        metric_c = pick(cols, [], metric)
    else:
        metric_c = None
        for h in METRIC_HINTS:
            for c in cols:
                if h in c.lower() and c not in (date_c, title_c):
                    vals = [to_number(r[c]) for r in rows]
                    if sum(v is not None for v in vals) >= max(2, len(rows) // 2):
                        metric_c = c
                        break
            if metric_c:
                break
    if not metric_c:
        raise SystemExit("No numeric metric column found. Use --metric. Columns: " + ", ".join(cols))
    items = []
    skipped = 0
    for i, r in enumerate(rows, 2):
        v = to_number(r.get(metric_c))
        label = (r.get(title_c) or "").strip().lower() if title_c else ""
        if label in {"total", "totals", "grand total", "overall"}:
            v = None  # summary row, not a post
        if v is None:
            skipped += 1
            continue
        items.append({"line": i, "value": v,
                      "title": (r.get(title_c) or "(untitled)").strip() if title_c else "row %d" % i,
                      "date": to_date(r.get(date_c)) if date_c else None})
    if len(items) < 4:
        raise SystemExit("Only %d usable rows: too few for conclusions." % len(items))
    vals = [x["value"] for x in items]
    med = statistics.median(vals)
    res = {"metric": metric_c, "title_col": title_c, "date_col": date_c, "rows": len(items),
           "skipped": skipped, "median": med, "mean": statistics.mean(vals), "total": sum(vals)}
    ranked = sorted(items, key=lambda x: -x["value"])
    res["top"] = ranked[:top]
    res["bottom"] = ranked[-top:][::-1]
    res["standouts"] = [x for x in ranked if med > 0 and x["value"] >= 2 * med][:top]
    dated = sorted([x for x in items if x["date"]], key=lambda x: x["date"])
    res["trend"] = None
    res["weekday"] = None
    if len(dated) >= 6:
        half = len(dated) // 2
        a = statistics.median([x["value"] for x in dated[:half]])
        b = statistics.median([x["value"] for x in dated[half:]])
        res["trend"] = {"first_half_median": a, "second_half_median": b,
                        "change_pct": ((b - a) / a * 100) if a else None,
                        "from": dated[0]["date"].date().isoformat(),
                        "to": dated[-1]["date"].date().isoformat()}
        by = {}
        for x in dated:
            by.setdefault(x["date"].strftime("%A"), []).append(x["value"])
        res["weekday"] = sorted(((d, statistics.median(v), len(v)) for d, v in by.items()),
                                key=lambda t: -t[1])
    return res


def fmt(n):
    return "%.1f" % n if abs(n) < 100 and n != int(n) else "{:,.0f}".format(n)


def render(res):
    L = ["# Analytics digest", "",
         "Metric: **%s** | rows used: %d (skipped: %d)" % (res["metric"], res["rows"], res["skipped"]),
         "Median: %s | mean: %s | total: %s" % (fmt(res["median"]), fmt(res["mean"]), fmt(res["total"])), ""]
    L.append("## Best")
    for x in res["top"]:
        L.append("- %s: %s (line %d)" % (x["title"][:80], fmt(x["value"]), x["line"]))
    L.append("")
    L.append("## Weakest")
    for x in res["bottom"]:
        L.append("- %s: %s (line %d)" % (x["title"][:80], fmt(x["value"]), x["line"]))
    L.append("")
    L.append("## Standouts (at least 2x the median)")
    L += ["- %s: %s" % (x["title"][:80], fmt(x["value"])) for x in res["standouts"]] or ["- none"]
    L.append("")
    t = res["trend"]
    if t:
        ch = "n/a" if t["change_pct"] is None else "%+.0f%%" % t["change_pct"]
        L.append("## Trend (%s to %s)" % (t["from"], t["to"]))
        L.append("- Median of first half: %s, second half: %s, change: %s" %
                 (fmt(t["first_half_median"]), fmt(t["second_half_median"]), ch))
        L.append("")
        L.append("## Weekday (median, n posts) - small samples, treat as hints")
        L += ["- %s: %s (n=%d)" % (d, fmt(m), n) for d, m, n in res["weekday"]]
    else:
        L.append("## Trend\n- Not enough dated rows (need 6+).")
    return "\n".join(L)


def selftest():
    sample = ("Video title,Publish date,Views,Impressions click-through rate (%)\n"
              "Intro to knitting,2026-01-05,\"1,200\",4.1%\n"
              "Yarn haul,2026-01-12,900,3.9%\n"
              "Blocking tips,2026-01-19,1100,4.0%\n"
              "Sweater pattern,2026-01-26,3500,6.2%\n"
              "Needle review,2026-02-02,1500,4.4%\n"
              "Colour theory,2026-02-09,1800,4.8%\n"
              "Q&A,2026-02-16,2.4K,5.0%\n"
              "Total,,,\n")
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(sample)
        p = f.name
    try:
        res = analyse(read_rows(p))
        assert res["metric"] == "Views", res["metric"]
        assert res["rows"] == 7 and res["skipped"] == 1, (res["rows"], res["skipped"])
        assert res["top"][0]["title"] == "Sweater pattern"
        assert res["standouts"] and res["standouts"][0]["title"] == "Sweater pattern"
        assert res["trend"]["change_pct"] > 0
        assert to_number("1,234") == 1234 and to_number("12,5%") == 12.5 and to_number("2.4K") == 2400
        print(render(res))
        print("\nSELFTEST OK")
    finally:
        os.unlink(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--metric"); ap.add_argument("--title"); ap.add_argument("--date")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.csv:
        ap.error("CSV path required")
    print(render(analyse(read_rows(a.csv), a.metric, a.title, a.date, a.top)))


if __name__ == "__main__":
    main()
