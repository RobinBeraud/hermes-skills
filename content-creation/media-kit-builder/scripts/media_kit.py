#!/usr/bin/env python3
"""Build a printable one-page HTML media kit from creator-supplied facts.

Rules the script enforces:
  * It never invents a number. Every figure is copied from the input file.
  * Every platform figure needs an "as_of" date and ideally a "source".
  * Empty sections are left out instead of filled with placeholders.
  * Leftover placeholders (TODO, XXX, ???) stop the build.

Usage:
  media_kit.py --init kit.json          write an example input file
  media_kit.py kit.json --out kit.html  build the kit
  media_kit.py --selftest               run built-in tests
Standard library only.
"""
import argparse, datetime, html, json, re, sys, os, tempfile

STALE_DAYS = 90
PLACEHOLDER = re.compile(r"\b(TODO|TBD|XXX+)\b|\?\?\?|lorem ipsum", re.I)

EXAMPLE = {
    "name": "Alex Example",
    "tagline": "Plain-language personal finance videos",
    "bio": "I make short videos that explain money topics without jargon. Based in Exampleville.",
    "contact": {"email": "alex@example.com", "website": "https://example.com"},
    "platforms": [
        {"name": "YouTube", "handle": "@alexexample", "audience": "12,400 subscribers",
         "as_of": "2026-11-01", "source": "YouTube Studio"},
        {"name": "Instagram", "handle": "@alex.example", "audience": "5,100 followers",
         "as_of": "2026-11-01", "source": "Instagram Insights"}
    ],
    "audience": [
        {"label": "Top country", "value": "Example Land (40%)", "as_of": "2026-11-01", "source": "YouTube Studio"}
    ],
    "top_content": [
        {"title": "Budgeting in 10 minutes", "note": "Most watched video of the last 90 days",
         "metric": "21,000 views", "as_of": "2026-11-01", "source": "YouTube Studio"}
    ],
    "past_collaborations": [{"brand": "Example Brand", "what": "One sponsored video (disclosed as an ad)"}],
    "services": [
        {"name": "Sponsored video", "details": "Up to 60 seconds, one revision", "price": "From 500 EUR"}
    ],
    "disclosure": "Every paid collaboration is clearly labelled as an ad."
}


def esc(x):
    return html.escape(str(x), quote=True)


def parse_date(s):
    try:
        return datetime.date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")


def check(data, today=None):
    """Return (errors, warnings). Errors block the build."""
    today = today or datetime.date.today()
    errors, warns = [], []
    if not str(data.get("name", "")).strip():
        errors.append("name is required")
    for p, s in walk_strings(data):
        if PLACEHOLDER.search(s):
            errors.append(f"placeholder text left in {p}: {s[:40]!r}")
    contact = data.get("contact") or {}
    if not any(str(v).strip() for v in contact.values()):
        warns.append("no contact details: a media kit without a contact is a dead end")

    def need_date(kind, i, item, figure_key):
        if not str(item.get(figure_key, "")).strip():
            return
        label = f"{kind}[{i}]"
        d = parse_date(item.get("as_of"))
        if not item.get("as_of"):
            errors.append(f"{label}: figure given without as_of date (use YYYY-MM-DD)")
        elif d is None:
            errors.append(f"{label}: as_of {item.get('as_of')!r} is not a YYYY-MM-DD date")
        else:
            if d > today:
                errors.append(f"{label}: as_of date is in the future")
            elif (today - d).days > STALE_DAYS:
                warns.append(f"{label}: figure is {(today - d).days} days old, refresh before sending")
        if not str(item.get("source", "")).strip():
            warns.append(f"{label}: no source named (brands trust 'YouTube Studio' more than nothing)")

    for i, it in enumerate(data.get("platforms") or []):
        need_date("platforms", i, it, "audience")
    for i, it in enumerate(data.get("audience") or []):
        need_date("audience", i, it, "value")
    for i, it in enumerate(data.get("top_content") or []):
        need_date("top_content", i, it, "metric")
    if (data.get("past_collaborations") or []) and not str(data.get("disclosure", "")).strip():
        warns.append("past collaborations listed but no disclosure statement")
    if not (data.get("platforms") or []):
        warns.append("no platforms listed")
    if (data.get("services") or []) and not any(str(s.get("price", "")).strip() for s in data["services"]):
        warns.append("services have no prices: fine if you prefer 'on request', but say so")
    return errors, warns


CSS = """
@page { size: A4; margin: 14mm; }
body { font-family: Helvetica, Arial, sans-serif; color: #1c1c1c; max-width: 780px; margin: 24px auto; padding: 0 16px; line-height: 1.45; }
h1 { font-size: 2rem; margin: 0; }
.tag { color: #555; margin: 2px 0 14px; font-size: 1.1rem; }
h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: .08em; border-bottom: 2px solid #1c1c1c; padding-bottom: 3px; margin-top: 26px; }
.grid { display: flex; flex-wrap: wrap; gap: 12px; }
.card { border: 1px solid #ccc; border-radius: 6px; padding: 10px 14px; min-width: 200px; flex: 1; }
.big { font-size: 1.3rem; font-weight: bold; }
.meta { color: #666; font-size: .8rem; }
table { border-collapse: collapse; width: 100%; }
td, th { text-align: left; padding: 6px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }
.foot { margin-top: 28px; font-size: .85rem; color: #444; border-top: 1px solid #ccc; padding-top: 8px; }
@media print { body { margin: 0; } }
"""


def meta_line(it):
    bits = []
    if it.get("as_of"):
        bits.append(f"as of {esc(it['as_of'])}")
    if it.get("source"):
        bits.append(f"source: {esc(it['source'])}")
    return f'<div class="meta">{", ".join(bits)}</div>' if bits else ""


def render(data):
    o = []
    o.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    o.append(f"<title>{esc(data['name'])} - Media kit</title><style>{CSS}</style></head><body>")
    o.append(f"<h1>{esc(data['name'])}</h1>")
    if data.get("tagline"):
        o.append(f"<p class='tag'>{esc(data['tagline'])}</p>")
    if data.get("bio"):
        o.append(f"<p>{esc(data['bio'])}</p>")
    plats = [p for p in data.get("platforms") or [] if str(p.get("audience", "")).strip() or p.get("handle")]
    if plats:
        o.append("<h2>Where to find me</h2><div class='grid'>")
        for p in plats:
            o.append("<div class='card'>")
            o.append(f"<div><strong>{esc(p.get('name', ''))}</strong> {esc(p.get('handle', ''))}</div>")
            if str(p.get("audience", "")).strip():
                o.append(f"<div class='big'>{esc(p['audience'])}</div>")
            o.append(meta_line(p) + "</div>")
        o.append("</div>")
    aud = [a for a in data.get("audience") or [] if str(a.get("value", "")).strip()]
    if aud:
        o.append("<h2>Audience</h2><table>")
        for a in aud:
            o.append(f"<tr><th>{esc(a.get('label', ''))}</th><td>{esc(a['value'])}{meta_line(a)}</td></tr>")
        o.append("</table>")
    top = [t for t in data.get("top_content") or [] if t.get("title")]
    if top:
        o.append("<h2>Best content</h2><table>")
        for t in top:
            line = esc(t["title"])
            if t.get("metric"):
                line += f" &mdash; <strong>{esc(t['metric'])}</strong>"
            note = f"<div>{esc(t['note'])}</div>" if t.get("note") else ""
            o.append(f"<tr><td>{line}{note}{meta_line(t)}</td></tr>")
        o.append("</table>")
    col = [c for c in data.get("past_collaborations") or [] if c.get("brand")]
    if col:
        o.append("<h2>Past collaborations</h2><ul>")
        for c in col:
            o.append(f"<li><strong>{esc(c['brand'])}</strong>" + (f": {esc(c['what'])}" if c.get("what") else "") + "</li>")
        o.append("</ul>")
    svc = [s for s in data.get("services") or [] if s.get("name")]
    if svc:
        o.append("<h2>Services</h2><table>")
        for s in svc:
            o.append(f"<tr><th>{esc(s['name'])}</th><td>{esc(s.get('details', ''))}</td><td>{esc(s.get('price', ''))}</td></tr>")
        o.append("</table>")
    contact = {k: v for k, v in (data.get("contact") or {}).items() if str(v).strip()}
    foot = []
    if data.get("disclosure"):
        foot.append(f"<p>{esc(data['disclosure'])}</p>")
    if contact:
        foot.append("<p>" + " &middot; ".join(f"{esc(k.title())}: {esc(v)}" for k, v in contact.items()) + "</p>")
    if foot:
        o.append("<div class='foot'>" + "".join(foot) + "</div>")
    o.append("</body></html>")
    return "\n".join(o)


def build(data, out, today=None):
    errors, warns = check(data, today)
    for w in warns:
        print("WARN:", w, file=sys.stderr)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 1
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(data))
    print(f"wrote {out} ({len(warns)} warning(s))")
    return 0


def selftest():
    today = datetime.date(2026, 11, 14)
    ok = True

    def t(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok = ok and cond

    e, w = check(EXAMPLE, today)
    t("example kit has no errors", not e)
    bad = json.loads(json.dumps(EXAMPLE)); del bad["platforms"][0]["as_of"]
    e, _ = check(bad, today); t("missing as_of blocks build", any("as_of" in x for x in e))
    bad = json.loads(json.dumps(EXAMPLE)); bad["bio"] = "TODO write bio"
    e, _ = check(bad, today); t("TODO placeholder blocks build", any("placeholder" in x for x in e))
    old = json.loads(json.dumps(EXAMPLE)); old["platforms"][0]["as_of"] = "2026-01-01"
    e, w = check(old, today); t("stale figure only warns", not e and any("days old" in x for x in w))
    fut = json.loads(json.dumps(EXAMPLE)); fut["platforms"][0]["as_of"] = "2027-01-01"
    e, _ = check(fut, today); t("future date blocks build", any("future" in x for x in e))
    xss = json.loads(json.dumps(EXAMPLE)); xss["name"] = "<script>alert(1)</script>"
    t("html is escaped", "<script>alert" not in render(xss))
    t("figures copied verbatim", "12,400 subscribers" in render(EXAMPLE))
    sparse = {"name": "Sam Sample", "contact": {"email": "sam@example.com"}}
    r = render(sparse)
    t("empty sections omitted", "Services" not in r and "Audience" not in r)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "k.html")
        t("build writes file", build(EXAMPLE, p, today) == 0 and os.path.getsize(p) > 500)
    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="JSON file with your facts")
    ap.add_argument("--out", default="media-kit.html")
    ap.add_argument("--init", metavar="FILE", help="write an example input file and exit")
    ap.add_argument("--check-only", action="store_true", help="validate, do not write HTML")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.init:
        if os.path.exists(a.init):
            print(f"{a.init} exists, not overwriting", file=sys.stderr); return 1
        with open(a.init, "w", encoding="utf-8") as f:
            json.dump(EXAMPLE, f, indent=2, ensure_ascii=False)
        print(f"wrote example to {a.init}: replace every value with your real facts"); return 0
    if not a.input:
        ap.print_help(); return 2
    try:
        with open(a.input, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as ex:
        print("cannot read input:", ex, file=sys.stderr); return 2
    if a.check_only:
        e, w = check(data)
        for x in w: print("WARN:", x)
        for x in e: print("ERROR:", x)
        return 1 if e else 0
    return build(data, a.out)


if __name__ == "__main__":
    sys.exit(main())
