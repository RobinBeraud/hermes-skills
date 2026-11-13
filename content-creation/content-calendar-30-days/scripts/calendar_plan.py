#!/usr/bin/env python3
"""Build a 30-day content calendar skeleton from pillars, platforms and a posting rhythm.

The script only does the mechanical part (dates, rotation, format mix, recycling
slots, balance check). Topics are left as TODO for the agent/creator to fill.
Standard library only.
"""
import argparse
import csv
import datetime as dt
import io
import math
import sys

DEFAULT_FORMATS = {
    "instagram": ["carousel", "reel", "single image", "story series"],
    "tiktok": ["short video", "talking head", "behind the scenes"],
    "linkedin": ["text post", "document carousel", "poll", "short video"],
    "youtube": ["long video", "short", "community-style update"],
    "x": ["thread", "single post", "poll"],
    "newsletter": ["essay", "link roundup"],
    "blog": ["how-to article", "opinion piece"],
}
FALLBACK_FORMATS = ["short post", "long post", "video"]
COLUMNS = ["date", "weekday", "platform", "pillar", "format", "topic", "recycle_from", "status"]


def post_weekdays(per_week):
    """Evenly spread weekday indexes (0=Mon) for N posts per week."""
    per_week = max(1, min(7, per_week))
    return sorted({round(i * 7 / per_week) % 7 for i in range(per_week)})


def build(pillars, platforms, start, days, per_week, recycle_every):
    wd = set(post_weekdays(per_week))
    rows = []
    n = 0
    fmt_idx = {p: 0 for p in platforms}
    for offset in range(days):
        day = start + dt.timedelta(days=offset)
        if day.weekday() not in wd:
            continue
        pillar = pillars[n % len(pillars)]
        # shift the platform each full cycle so a pillar is not stuck on one platform
        cycle = len(pillars) * len(platforms) // math.gcd(len(pillars), len(platforms))
        platform = platforms[(n + n // cycle) % len(platforms)]
        fmts = DEFAULT_FORMATS.get(platform.lower(), FALLBACK_FORMATS)
        fmt = fmts[fmt_idx[platform] % len(fmts)]
        fmt_idx[platform] += 1
        n += 1
        recycle = ""
        topic = "TODO"
        if recycle_every and n % recycle_every == 0:
            recycle = "TODO: best past post on this pillar"
            topic = "TODO: new angle on the recycled post"
        rows.append({
            "date": day.isoformat(), "weekday": day.strftime("%a"), "platform": platform,
            "pillar": pillar, "format": fmt, "topic": topic, "recycle_from": recycle,
            "status": "idea",
        })
    return rows


def balance_report(rows, pillars, platforms):
    lines = []
    total = len(rows)
    lines.append(f"Posts planned: {total}")
    for p in pillars:
        c = sum(1 for r in rows if r["pillar"] == p)
        lines.append(f"  pillar {p}: {c} ({(100 * c // total) if total else 0}%)")
    for p in platforms:
        c = sum(1 for r in rows if r["platform"] == p)
        lines.append(f"  platform {p}: {c}")
    rec = sum(1 for r in rows if r["recycle_from"])
    lines.append(f"  recycling slots: {rec}")
    warn = []
    for a, b in zip(rows, rows[1:]):
        if a["pillar"] == b["pillar"] and len(pillars) > 1:
            warn.append(f"same pillar twice in a row: {a['date']} and {b['date']}")
    counts = [sum(1 for r in rows if r["pillar"] == p) for p in pillars]
    if counts and max(counts) - min(counts) > 1:
        warn.append("pillars are unbalanced by more than one post")
    return lines, warn


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def to_md(rows):
    out = ["| Date | Day | Platform | Pillar | Format | Topic | Recycle from |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| {date} | {weekday} | {platform} | {pillar} | {format} | {topic} | {recycle_from} |".format(**r))
    return "\n".join(out) + "\n"


def check_file(path):
    """Check a filled-in calendar CSV: empty topics, duplicates, same pillar streaks."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    problems = []
    seen = {}
    for i, r in enumerate(rows, start=2):
        t = (r.get("topic") or "").strip()
        if not t or t.upper().startswith("TODO"):
            problems.append(f"line {i}: topic still empty ({r.get('date')})")
        elif t.lower() in seen:
            problems.append(f"line {i}: topic duplicates line {seen[t.lower()]}")
        else:
            seen[t.lower()] = i
        if r.get("recycle_from", "").strip().upper().startswith("TODO"):
            problems.append(f"line {i}: recycling slot has no source post")
    for a, b in zip(rows, rows[1:]):
        if a.get("pillar") == b.get("pillar"):
            problems.append(f"same pillar back to back: {a.get('date')} and {b.get('date')}")
    return len(rows), problems


def selftest():
    start = dt.date(2026, 12, 1)  # a Tuesday
    rows = build(["Teach", "Story", "Proof"], ["instagram", "linkedin"], start, 30, 3, 5)
    assert rows, "no rows"
    assert all(start <= dt.date.fromisoformat(r["date"]) < start + dt.timedelta(days=30) for r in rows)
    assert 12 <= len(rows) <= 14, len(rows)
    assert post_weekdays(3) == [0, 2, 5] or len(post_weekdays(3)) == 3
    assert sum(1 for r in rows if r["recycle_from"]) == len(rows) // 5
    lines, warn = balance_report(rows, ["Teach", "Story", "Proof"], ["instagram", "linkedin"])
    assert not any("twice" in w for w in warn), warn
    csv_text = to_csv(rows)
    assert csv_text.splitlines()[0] == ",".join(COLUMNS)
    import tempfile, os
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as tf:
        tf.write(csv_text)
        name = tf.name
    n, problems = check_file(name)
    os.unlink(name)
    assert n == len(rows) and problems, "check should flag TODO topics"
    print("selftest OK:", len(rows), "posts")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pillars", help="comma-separated content pillars, e.g. 'Teach,Story,Proof'")
    ap.add_argument("--platforms", default="instagram", help="comma-separated platforms")
    ap.add_argument("--start", help="start date YYYY-MM-DD (default: tomorrow)")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--per-week", type=int, default=3, help="posting days per week (1-7)")
    ap.add_argument("--recycle-every", type=int, default=5, help="every Nth post is a recycling slot (0 = none)")
    ap.add_argument("--format", choices=["csv", "md"], default="csv")
    ap.add_argument("--out", help="write to this file instead of stdout")
    ap.add_argument("--check", metavar="CSV", help="check a filled-in calendar CSV")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if a.check:
        n, problems = check_file(a.check)
        print(f"{n} rows checked")
        for p in problems:
            print("PROBLEM:", p)
        return 1 if problems else 0
    if not a.pillars:
        ap.error("--pillars is required")
    pillars = [p.strip() for p in a.pillars.split(",") if p.strip()]
    platforms = [p.strip() for p in a.platforms.split(",") if p.strip()]
    start = dt.date.fromisoformat(a.start) if a.start else dt.date.today() + dt.timedelta(days=1)
    rows = build(pillars, platforms, start, a.days, a.per_week, a.recycle_every)
    text = to_csv(rows) if a.format == "csv" else to_md(rows)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    lines, warn = balance_report(rows, pillars, platforms)
    print("\n".join(lines), file=sys.stderr)
    for w in warn:
        print("WARNING:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
