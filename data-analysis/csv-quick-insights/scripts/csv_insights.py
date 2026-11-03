#!/usr/bin/env python3
"""csv_insights.py - quick profile of a CSV file using only the standard library.

Reports: delimiter, row/column counts, inferred types, missing values,
duplicate rows, numeric outliers (IQR rule), top categories, and three
text charts (missing values per column, histogram of the first numeric
column, top values of the first categorical column).

Usage:
  csv_insights.py FILE.csv [--delimiter ,] [--json] [--max-rows N]
  csv_insights.py --selftest
"""
import argparse
import csv
import io
import json
import math
import re
import statistics
import sys
from collections import Counter

MISSING = {"", "na", "n/a", "nan", "null", "none", "-", "?"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?$|^\d{2}/\d{2}/\d{4}$")
BOOL = {"true", "false", "yes", "no", "0", "1", "y", "n"}


def is_missing(v):
    return v is None or v.strip().lower() in MISSING


def to_float(v):
    try:
        return float(v.strip().replace(",", "") if v.count(",") > 0 and v.count(".") > 0 else v.strip())
    except ValueError:
        return None


def infer_type(values):
    vals = [v.strip() for v in values if not is_missing(v)]
    if not vals:
        return "empty"
    if all(v.lower() in BOOL for v in vals) and len(set(v.lower() for v in vals)) <= 2:
        return "boolean"
    if all(re.fullmatch(r"[+-]?\d+", v) for v in vals):
        return "integer"
    if all(to_float(v) is not None for v in vals):
        return "float"
    if all(DATE_RE.match(v) for v in vals):
        return "date"
    distinct = len(set(vals))
    if distinct <= max(10, len(vals) // 5):
        return "category"
    return "text"


def sniff(sample, forced):
    if forced:
        return forced
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def bar(n, total, width=30):
    return "#" * (0 if total == 0 else max(1 if n else 0, round(width * n / total)))


def analyse(text, delimiter=None, max_rows=None):
    delim = sniff(text[:4096], delimiter)
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    if not rows:
        return {"error": "empty file"}
    header, body = rows[0], rows[1:]
    if max_rows:
        body = body[:max_rows]
    ncol = len(header)
    ragged = sum(1 for r in body if len(r) != ncol)
    body = [(r + [""] * ncol)[:ncol] for r in body]
    dup = len(body) - len(set(tuple(r) for r in body))
    cols = []
    for i, name in enumerate(header):
        vals = [r[i] for r in body]
        miss = sum(1 for v in vals if is_missing(v))
        t = infer_type(vals)
        info = {"name": name, "type": t, "missing": miss,
                "missing_pct": round(100 * miss / len(vals), 1) if vals else 0.0,
                "distinct": len({v for v in vals if not is_missing(v)})}
        if t in ("integer", "float"):
            nums = [to_float(v) for v in vals if not is_missing(v)]
            q = statistics.quantiles(nums, n=4) if len(nums) >= 2 else [nums[0]] * 3
            iqr = q[2] - q[0]
            lo, hi = q[0] - 1.5 * iqr, q[2] + 1.5 * iqr
            info.update(min=min(nums), max=max(nums), mean=round(statistics.fmean(nums), 4),
                        median=statistics.median(nums), outliers=sum(1 for x in nums if x < lo or x > hi))
            info["_nums"] = nums
        elif t in ("category", "boolean", "text"):
            info["top"] = Counter(v for v in vals if not is_missing(v)).most_common(5)
        cols.append(info)
    return {"delimiter": delim, "rows": len(body), "columns": ncol, "ragged_rows": ragged,
            "duplicate_rows": dup, "cols": cols}


def render(res):
    out = []
    d = "TAB" if res["delimiter"] == "\t" else res["delimiter"]
    out.append(f"Rows: {res['rows']}  Columns: {res['columns']}  Delimiter: {d}")
    out.append(f"Duplicate rows: {res['duplicate_rows']}  Rows with wrong field count: {res['ragged_rows']}")
    out.append("")
    out.append("Columns")
    for c in res["cols"]:
        line = f"- {c['name']} [{c['type']}] missing={c['missing']} ({c['missing_pct']}%) distinct={c['distinct']}"
        if "mean" in c:
            line += f" min={c['min']:g} median={c['median']:g} mean={c['mean']:g} max={c['max']:g} outliers={c['outliers']}"
        elif c.get("top"):
            line += " top=" + ", ".join(f"{k}:{n}" for k, n in c["top"][:3])
        out.append(line)
    out.append("")
    out.append("Chart 1: missing values per column")
    n = res["rows"]
    for c in res["cols"]:
        out.append(f"{c['name'][:20]:<20} {bar(c['missing'], n):<30} {c['missing']}")
    numeric = [c for c in res["cols"] if "_nums" in c]
    # skip identifier-like columns (named id/index) when another numeric column exists
    def idlike(c):
        return bool(re.search(r"(^|_)(id|index)$", c["name"].lower()))
    num = next((c for c in numeric if not idlike(c)), numeric[0] if numeric else None)
    if num:
        nums = num["_nums"]
        lo, hi = min(nums), max(nums)
        k = 8 if lo != hi else 1
        w = (hi - lo) / k or 1
        counts = [0] * k
        for x in nums:
            counts[min(int((x - lo) / w), k - 1)] += 1
        out.append("")
        out.append(f"Chart 2: histogram of '{num['name']}'")
        for j, cnt in enumerate(counts):
            out.append(f"{lo + j * w:>12.4g} {bar(cnt, max(counts)):<30} {cnt}")
    cat = next((c for c in res["cols"] if c["type"] == "category" and c.get("top")), None)
    if cat:
        out.append("")
        out.append(f"Chart 3: top values of '{cat['name']}'")
        mx = cat["top"][0][1]
        for k_, cnt in cat["top"]:
            out.append(f"{str(k_)[:20]:<20} {bar(cnt, mx):<30} {cnt}")
    return "\n".join(out)


SAMPLE = """id,city,price,signup,active,note
1,Paris,100,2024-01-03,yes,ok
2,Lyon,110,2024-01-04,no,
3,Paris,95,2024-01-05,yes,fine
4,Nice,105,2024-01-06,yes,
5,Paris,98,2024-01-07,no,ok
6,Lyon,2000,2024-01-08,yes,
7,Paris,,2024-01-09,yes,
7,Paris,,2024-01-09,yes,
"""


def selftest():
    r = analyse(SAMPLE)
    by = {c["name"]: c for c in r["cols"]}
    assert r["rows"] == 8 and r["columns"] == 6, r
    assert r["duplicate_rows"] == 1
    assert by["id"]["type"] == "integer"
    assert by["price"]["type"] == "integer" and by["price"]["missing"] == 2
    assert by["price"]["outliers"] == 1, by["price"]
    assert by["city"]["type"] == "category" and by["city"]["top"][0] == ("Paris", 5)
    assert by["signup"]["type"] == "date"
    assert by["active"]["type"] == "boolean"
    assert analyse("a;b\n1;2\n3;4\n")["delimiter"] == ";"
    assert "error" in analyse("")
    print(render(r))
    print("\nSELFTEST OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--delimiter")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-rows", type=int)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("FILE required (or --selftest)")
    with open(a.file, newline="", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    res = analyse(text, a.delimiter, a.max_rows)
    if "error" in res:
        sys.exit(res["error"])
    if a.json:
        for c in res["cols"]:
            c.pop("_nums", None)
        print(json.dumps(res, indent=2, default=str))
    else:
        print(render(res))


if __name__ == "__main__":
    main()
