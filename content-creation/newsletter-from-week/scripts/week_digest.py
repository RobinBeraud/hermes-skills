#!/usr/bin/env python3
"""Turn a CSV of this week's posts into a newsletter skeleton (Markdown).

CSV columns (header row required): date,title,url,summary,favorite
- date: YYYY-MM-DD
- favorite: optional, any non-empty value other than no/false/0 marks a pick
Standard library only. Never invents text: missing summaries are flagged.
"""
import argparse, csv, datetime as dt, io, sys
from urllib.parse import urlsplit, urlunsplit

def norm_url(u):
    p = urlsplit(u.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))

def load(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    need = {"date", "title", "url"}
    if not rows and not text.strip():
        raise SystemExit("empty CSV")
    missing = need - set(rows[0].keys() if rows else csv.reader(io.StringIO(text)).__next__())
    if missing:
        raise SystemExit("missing columns: " + ", ".join(sorted(missing)))
    return rows

def build(rows, start, end, name):
    seen, items, notes = set(), [], []
    for r in rows:
        try:
            d = dt.date.fromisoformat((r.get("date") or "").strip())
        except ValueError:
            notes.append(f"skipped (bad date): {r.get('title','?')!r}")
            continue
        if not (start <= d <= end):
            continue
        key = norm_url(r.get("url") or "")
        if not key or not key.startswith(("http://", "https://")):
            notes.append(f"skipped (bad URL): {r.get('title','?')!r}")
            continue
        if key in seen:
            notes.append(f"skipped (duplicate URL): {r.get('title','?')!r}")
            continue
        seen.add(key)
        fav = (r.get("favorite") or "").strip().lower() not in ("", "no", "false", "0", "n")
        items.append((d, r["title"].strip(), r["url"].strip(), (r.get("summary") or "").strip(), fav))
    items.sort(key=lambda x: x[0])
    out = [f"# {name}: week of {start.isoformat()}", "",
           "SUBJECT OPTIONS: (agent: write 3, based only on the titles below)", "",
           "INTRO: (agent: 2 sentences in your own voice, no claims about numbers)", ""]
    favs = [i for i in items if i[4]]
    if favs:
        d, t, u, s, _ = favs[0]
        out += ["## Pick of the week", f"[{t}]({u})", s or "TODO: summary missing, ask the creator", ""]
    out += ["## This week's posts", ""]
    for d, t, u, s, f in items:
        out.append(f"- **[{t}]({u})** ({d.isoformat()}): " + (s or "TODO: summary missing, ask the creator"))
    out += ["", "OUTRO: (agent: one question or call to reply)", ""]
    if not items:
        notes.append("no posts in range")
    if len(favs) > 1:
        notes.append(f"{len(favs)} favorites marked, only the first is used as Pick of the week")
    todo = sum(1 for i in items if not i[3])
    if todo:
        notes.append(f"{todo} post(s) without a summary")
    return "\n".join(out), notes, len(items)

def selftest():
    csvtext = ("date,title,url,summary,favorite\n"
        "2026-03-02,Post A,https://example.com/a/,Short A,\n"
        "2026-03-03,Post A again,https://EXAMPLE.com/a?utm=x,Dup,\n"
        "2026-03-04,Post B,https://example.com/b,,yes\n"
        "2026-03-20,Old post,https://example.com/old,Old,\n"
        "not-a-date,Bad,https://example.com/bad,x,\n"
        "2026-03-05,No url,,x,\n")
    md, notes, n = build(load(csvtext), dt.date(2026,3,2), dt.date(2026,3,8), "Test Letter")
    assert n == 2, n
    assert "Pick of the week" in md and "example.com/b" in md
    assert "TODO: summary missing" in md
    assert "Old post" not in md
    assert any("duplicate" in x for x in notes) and any("bad date" in x for x in notes) and any("bad URL" in x for x in notes)
    print(md); print("\nNOTES:", *notes, sep="\n- "); print("\nSELFTEST OK")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", help="CSV file of posts")
    ap.add_argument("--start", help="first day YYYY-MM-DD (default: 6 days before --end)")
    ap.add_argument("--end", help="last day YYYY-MM-DD (default: today)")
    ap.add_argument("--name", default="Weekly letter")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.csv:
        ap.error("CSV file required")
    end = dt.date.fromisoformat(a.end) if a.end else dt.date.today()
    start = dt.date.fromisoformat(a.start) if a.start else end - dt.timedelta(days=6)
    with open(a.csv, newline="", encoding="utf-8-sig") as f:
        md, notes, n = build(load(f.read()), start, end, a.name)
    print(md)
    if notes:
        print("\n---\nNOTES FOR THE AGENT:", file=sys.stderr)
        for x in notes: print("- " + x, file=sys.stderr)
    sys.exit(0 if n else 1)

if __name__ == "__main__":
    main()
