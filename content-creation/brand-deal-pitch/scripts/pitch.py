#!/usr/bin/env python3
"""Build a brand partnership pitch email (plus a follow-up) from facts a creator provides.

What the script enforces:
  * Figures are copied verbatim from the brief, each with a date. Never invented.
  * Prices appear only if the creator supplied them.
  * Leftover placeholders (TODO, TBD, XXX, ???) stop the build.
  * Warnings for hype words, stale figures, numbers in free text that are not
    backed by a dated proof entry, a missing disclosure line, or a long email.

Usage:
  pitch.py --init brief.json            write an example brief (fictional data)
  pitch.py brief.json --check-only      only validate
  pitch.py brief.json --out pitch.md    write pitch + follow-up (Markdown/plain text)
  pitch.py --selftest                   run built-in tests
Standard library only.
"""
import argparse, copy, datetime, json, os, re, sys, tempfile

STALE_DAYS = 90
MAX_WORDS = 230
PLACEHOLDER = re.compile(r"\b(TODO|TBD|XXX+)\b|\?\?\?|lorem ipsum|\[(brand|name|your)[^\]]*\]", re.I)
HYPE = ["guaranteed", "game-changer", "game changer", "go viral", "going viral", "viral",
        "huge reach", "massive", "explode", "skyrocket", "best in the world", "revolutionary",
        "once in a lifetime", "no-brainer", "100%"]

EXAMPLE = {
    "creator": {"name": "Alex Example", "niche": "plain-language personal finance videos",
                "contact": "alex@example.com", "link": "https://example.com/media-kit"},
    "brand": {"name": "Example Budget App", "contact_name": "Sam",
              "why_this_brand": [
                  "I have used your envelope-budgeting feature for my own monthly planning since spring.",
                  "Your latest campaign explains money with everyday examples, which is how I teach too."]},
    "proof": [
        {"claim": "12,400 YouTube subscribers", "as_of": "2026-11-01", "source": "YouTube Studio"},
        {"claim": "Most watched video of the last 90 days: 21,000 views", "as_of": "2026-11-01", "source": "YouTube Studio"}],
    "ideas": [
        {"title": "Budget reset challenge", "format": "One 8-minute video + 3 short clips",
         "description": "I set up a real monthly budget in your app on camera and report honestly what worked and what did not."},
        {"title": "Common money myths", "format": "One carousel post",
         "description": "Five myths from my comments, answered with screenshots of the feature in use."}],
    "deliverables": [
        {"item": "1 dedicated video", "details": "labelled as an ad, one round of revisions"},
        {"item": "3 short clips", "details": "cut from the video, same label"}],
    "pricing": {"text": "My rate for this package is 1,200 EUR, usage rights for 3 months on your own channels.",
                "provided_by_creator": True},
    "timeline": "I can publish within 4 weeks of signing.",
    "disclosure": "All paid content is clearly labelled as an ad, with the label shown at the start.",
    "ask": "Would you be open to a 15-minute call next week to see whether this fits your plans?",
    "followup_days": 7
}


def parse_date(s):
    try:
        return datetime.datetime.strptime(str(s), "%Y-%m-%d").date()
    except ValueError:
        return None


def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from walk_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_strings(v)


def nums(text):
    return set(re.findall(r"\d[\d,.\u202f ]*\d|\d", text))


def norm(n):
    return re.sub(r"[^\d]", "", n)


def validate(b, today=None):
    today = today or datetime.date.today()
    errors, warns = [], []
    cr, br = b.get("creator", {}), b.get("brand", {})
    if not cr.get("name"): errors.append("creator.name is missing")
    if not cr.get("contact"): errors.append("creator.contact is missing (how should they reply?)")
    if not br.get("name"): errors.append("brand.name is missing")
    why = br.get("why_this_brand") or []
    if not why:
        errors.append("brand.why_this_brand is empty: a pitch with no specific reason is spam")
    for i, w in enumerate(why):
        if len(w.split()) < 6:
            warns.append(f"brand.why_this_brand[{i}] is very short; make it specific to this brand")
    ideas = b.get("ideas") or []
    if not ideas: errors.append("ideas is empty: propose at least one content idea")
    if len(ideas) > 3: warns.append("more than 3 ideas; brands read two or three at most")
    for i, it in enumerate(ideas):
        if not it.get("title") or not it.get("description"):
            errors.append(f"ideas[{i}] needs a title and a description")
    if not b.get("deliverables"): errors.append("deliverables is empty: say exactly what the brand receives")
    if not b.get("ask"): errors.append("ask is missing: end with one clear next step")

    proof_nums = set()
    for i, p in enumerate(b.get("proof") or []):
        d = parse_date(p.get("as_of"))
        if not p.get("claim"): errors.append(f"proof[{i}]: claim missing"); continue
        if d is None: errors.append(f"proof[{i}]: as_of must be YYYY-MM-DD")
        elif d > today: errors.append(f"proof[{i}]: as_of is in the future")
        elif (today - d).days > STALE_DAYS:
            warns.append(f"proof[{i}]: figure is {(today - d).days} days old, refresh before sending")
        if not p.get("source"): warns.append(f"proof[{i}]: no source named")
        proof_nums |= {norm(n) for n in nums(p["claim"])}
    if not b.get("proof"):
        warns.append("no proof entries: the email will contain no audience figures (fine, but say why you fit)")

    pr = b.get("pricing")
    if pr:
        if not pr.get("provided_by_creator"):
            errors.append("pricing.provided_by_creator must be true: the agent never invents a rate")
        proof_nums |= {norm(n) for n in nums(pr.get("text", ""))}
    else:
        warns.append("no pricing: the email will not quote a rate (asking for their budget is fine)")
    if not b.get("disclosure"):
        warns.append("no disclosure line: say that paid content is labelled as such")

    # free text checks
    free = []
    for w in why: free.append(("brand.why_this_brand", w))
    for i, it in enumerate(ideas):
        free.append((f"ideas[{i}]", " ".join(str(it.get(k, "")) for k in ("title", "format", "description"))))
    for i, dl in enumerate(b.get("deliverables") or []):
        free.append((f"deliverables[{i}]", " ".join(str(v) for v in dl.values())))
    free.append(("timeline", str(b.get("timeline", ""))))
    deliver_nums = set()
    for dl in b.get("deliverables") or []:
        deliver_nums |= {norm(n) for n in nums(str(dl.get("item", "")))}
    for where, text in free:
        for n in nums(text):
            k = norm(n)
            if k in proof_nums: continue
            if where.startswith(("deliverables", "ideas", "timeline")): continue  # counts and durations are plans, not claims
            warns.append(f"{where}: number '{n.strip()}' has no dated proof entry; remove it or add proof")
    for s in walk_strings(b):
        if PLACEHOLDER.search(s):
            errors.append(f"placeholder text found: {s[:60]!r}")
        low = s.lower()
        for h in HYPE:
            if re.search(r"(?<![a-z])" + re.escape(h) + r"(?![a-z])", low):
                warns.append(f"hype word '{h}' in: {s[:60]!r}")
    return errors, warns


def build(b):
    cr, br = b["creator"], b["brand"]
    greet = br.get("contact_name")
    hi = f"Hi {greet}," if greet else f"Hello {br['name']} team,"
    L = [hi, ""]
    L.append(f"I'm {cr['name']}" + (f", I make {cr['niche']}." if cr.get("niche") else "."))
    L.append("")
    L.append(f"Why {br['name']}:")
    for w in br["why_this_brand"]: L.append(f"- {w}")
    if b.get("proof"):
        L += ["", "A few facts about my audience (with date and source):"]
        for p in b["proof"]:
            L.append(f"- {p['claim']} (as of {p['as_of']}" + (f", {p['source']})" if p.get("source") else ")"))
    L += ["", "What I would make:"]
    for it in b["ideas"]:
        fmt = f" ({it['format']})" if it.get("format") else ""
        L.append(f"- {it['title']}{fmt}: {it['description']}")
    L += ["", "What you would receive:"]
    for d in b["deliverables"]:
        L.append(f"- {d['item']}" + (f", {d['details']}" if d.get("details") else ""))
    tail = []
    if b.get("pricing", {}).get("text"): tail.append(b["pricing"]["text"])
    if b.get("timeline"): tail.append(b["timeline"])
    if b.get("disclosure"): tail.append(b["disclosure"])
    if tail: L += ["", " ".join(tail)]
    L += ["", b["ask"], ""]
    if cr.get("link"): L += [f"Media kit: {cr['link']}", ""]
    L += [f"Thank you for your time,", cr["name"], cr["contact"]]
    body = "\n".join(L)
    subject = f"Partnership idea for {br['name']}: {b['ideas'][0]['title']}"
    days = b.get("followup_days", 7)
    f = [f"{hi}", "",
         f"Just a short follow-up on my note from {days} days ago about {b['ideas'][0]['title'].lower()}.",
         "If the timing is wrong or someone else handles creator partnerships, "
         "a pointer to the right person would help a lot.", "",
         b["ask"], "", "Thanks again,", cr["name"]]
    return subject, body, "\n".join(f), days


def render(b):
    subject, body, fu, days = build(b)
    words = len(body.split())
    out = f"# Pitch email\n\nSubject: {subject}\n\n{body}\n\n---\n\n# Follow-up (send after {days} days, only if no reply)\n\nSubject: Re: {subject}\n\n{fu}\n"
    return out, words


def run(path, out=None, check_only=False, today=None):
    b = json.load(open(path, encoding="utf-8"))
    errors, warns = validate(b, today)
    for w in warns: print("WARN:", w)
    for e in errors: print("ERROR:", e)
    if errors:
        print(f"{len(errors)} error(s): not built")
        return 1
    text, words = render(b)
    if words > MAX_WORDS:
        print(f"WARN: email body is {words} words (target under {MAX_WORDS}); trim ideas or reasons")
    if check_only:
        print("check OK" + (f" ({len(warns)} warning(s))" if warns else ""))
        return 0
    if out:
        open(out, "w", encoding="utf-8").write(text)
        print(f"wrote {out} ({words} words in the pitch body, {len(warns)} warning(s))")
    else:
        print(text)
    return 0


def selftest():
    ok = True
    def t(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok = ok and cond
    today = datetime.date(2026, 11, 15)
    b = copy.deepcopy(EXAMPLE)
    e, w = validate(b, today); t("example has no errors", not e)
    t("example has no warnings", not w)
    text, words = render(b)
    t("figures copied verbatim", "12,400 YouTube subscribers (as of 2026-11-01, YouTube Studio)" in text)
    t("price copied verbatim", "1,200 EUR" in text)
    t("follow-up present", "Follow-up" in text and "Re: " in text)
    t("example under word limit", words <= MAX_WORDS)
    c = copy.deepcopy(b); c["pricing"]["provided_by_creator"] = False
    t("invented price refused", any("never invents" in x for x in validate(c, today)[0]))
    c = copy.deepcopy(b); del c["pricing"]
    t("no pricing -> no rate in text", "EUR" not in render(c)[0] and any("no pricing" in x for x in validate(c, today)[1]))
    c = copy.deepcopy(b); c["proof"][0]["as_of"] = "2027-01-01"
    t("future date refused", any("future" in x for x in validate(c, today)[0]))
    c = copy.deepcopy(b); c["proof"][0]["as_of"] = "2026-01-01"
    t("stale figure warned", any("days old" in x for x in validate(c, today)[1]))
    c = copy.deepcopy(b); c["brand"]["why_this_brand"] = []
    t("missing reason refused", any("why_this_brand" in x for x in validate(c, today)[0]))
    c = copy.deepcopy(b); c["ask"] = "TODO"
    t("placeholder refused", any("placeholder" in x for x in validate(c, today)[0]))
    c = copy.deepcopy(b); c["brand"]["why_this_brand"][0] = "Your app is a game-changer and my audience of 50,000 will love it."
    w = validate(c, today)[1]
    t("hype word warned", any("game-changer" in x for x in w))
    t("unbacked number warned", any("50,000" in x for x in w))
    c = copy.deepcopy(b); c["ideas"] = c["ideas"] * 2
    t("too many ideas warned", any("more than 3" in x for x in validate(c, today)[1]))
    c = copy.deepcopy(b); del c["disclosure"]
    t("missing disclosure warned", any("disclosure" in x for x in validate(c, today)[1]))
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "b.json"); o = os.path.join(d, "o.md")
        json.dump(EXAMPLE, open(p, "w"))
        t("file build works", run(p, out=o, today=today) == 0 and os.path.getsize(o) > 200)
    print("ALL PASS" if ok else "SOME FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Build a brand partnership pitch from a creator's facts.")
    ap.add_argument("brief", nargs="?")
    ap.add_argument("--init", metavar="FILE")
    ap.add_argument("--out"); ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: sys.exit(selftest())
    if a.init:
        json.dump(EXAMPLE, open(a.init, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"wrote example brief to {a.init} (fictional data: replace every value)"); return
    if not a.brief: ap.error("give a brief.json, --init FILE, or --selftest")
    sys.exit(run(a.brief, a.out, a.check_only))

if __name__ == "__main__":
    main()
