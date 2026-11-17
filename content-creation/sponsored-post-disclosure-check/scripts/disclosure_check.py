#!/usr/bin/env python3
"""Check that a sponsored post shows its commercial relationship clearly.

Standard library only. Not legal advice: it applies a rules file YOU control.
Usage:
  disclosure_check.py POST.txt [--rules rules.json] [--platform instagram] [--json]
  disclosure_check.py --selftest
  disclosure_check.py --print-rules     # dump the default rules to edit
"""
import argparse, json, re, sys

DEFAULT_RULES = {
    "_note": "Editable starting point, NOT official platform or legal rules. Replace with the brief or the rules of your country/platform.",
    "clear_terms": ["#ad", "ad:", "#sponsored", "#paidpartnership", "paid partnership",
                    "sponsored", "advertisement", "paid promotion", "paid ad",
                    "in paid collaboration with", "i was paid", "this is an ad"],
    "ambiguous_terms": ["#sp", "#collab", "#collaboration", "#partner", "#ambassador",
                        "#brandpartner", "#thanks", "#gifted", "#affiliate",
                        "thanks to", "in partnership with", "in collaboration with",
                        "#brandambassador", "#sponsor"],
    "max_position_chars": {"default": 125, "instagram": 125, "tiktok": 100,
                           "linkedin": 140, "youtube": 100, "x": 100},
    "hashtag_block_limit": 5,
    "require_brand_mention": True
}

def words_in(text, term):
    t = term.lower()
    if t.startswith("#"):
        return [m.start() for m in re.finditer(re.escape(t) + r"(?![a-z0-9_])", text)]
    return [m.start() for m in re.finditer(r"(?<![a-z0-9_#])" + re.escape(t) + r"(?![a-z0-9_])", text)]

def check(post, rules, platform="default", brand=None):
    low = post.lower()
    limit = rules["max_position_chars"].get(platform, rules["max_position_chars"]["default"])
    findings = []
    clear = sorted((p, t) for t in rules["clear_terms"] for p in words_in(low, t))
    amb = sorted((p, t) for t in rules["ambiguous_terms"] for p in words_in(low, t))
    if not clear:
        if amb:
            findings.append(("FAIL", "only_ambiguous",
                "Only vague wording found (%s). Add an explicit term such as %s." %
                (", ".join(sorted({t for _, t in amb})), ", ".join(rules["clear_terms"][:3]))))
        else:
            findings.append(("FAIL", "missing", "No disclosure wording found."))
    else:
        pos, term = clear[0]
        if pos > limit:
            findings.append(("WARN", "late",
                "First clear term '%s' starts at character %d; the rule says it should appear within the first %d (%s)." % (term, pos, limit, platform)))
        else:
            findings.append(("PASS", "position", "Clear term '%s' appears at character %d (limit %d)." % (term, pos, limit)))
        # hidden in hashtag block?
        tags = list(re.finditer(r"#\w+", post))
        run = 0; best = 0; tail_start = None
        prev_end = None
        for m in tags:
            if prev_end is not None and post[prev_end:m.start()].strip() == "":
                run += 1
            else:
                run = 1
            prev_end = m.end(); best = max(best, run)
        if term.startswith("#") and best > rules["hashtag_block_limit"] and pos > limit:
            findings.append(("WARN", "buried", "The disclosure hashtag sits inside a block of %d hashtags, easy to miss." % best))
        if all(t.startswith("#") for _, t in clear):
            findings.append(("INFO", "hashtag_only", "Disclosure is hashtag-only; a plain sentence is easier to notice."))
    if rules.get("require_brand_mention") and brand:
        if brand.lower() not in low:
            findings.append(("WARN", "brand", "Brand '%s' is not named in the text." % brand))
    findings.append(("MANUAL", "native_label",
        "Check by hand: turn on the platform's own paid-partnership label if it exists, and compare with your contract/brief."))
    verdict = "FAIL" if any(f[0] == "FAIL" for f in findings) else ("WARN" if any(f[0] == "WARN" for f in findings) else "PASS")
    return verdict, findings

def render(verdict, findings):
    out = ["Verdict: " + verdict]
    for lvl, code, msg in findings:
        out.append("[%s] %s: %s" % (lvl, code, msg))
    out.append("Reminder: this is a text check against your rules, not legal advice.")
    return "\n".join(out)

def selftest():
    r = DEFAULT_RULES
    cases = [
        ("Ad: I tested the Acme bottle for a week. Notes below.", "PASS"),
        ("Loving my new bottle! " + "x" * 200 + " #ad", "WARN"),
        ("Thanks to @acme for this! #collab #partner", "FAIL"),
        ("Just a normal post about my day.", "FAIL"),
        ("#advent calendar day 3", "FAIL"),   # '#ad' must not match '#advent'
    ]
    bad = 0
    for text, want in cases:
        got, _ = check(text, r, "instagram")
        ok = got == want
        bad += not ok
        print(("ok  " if ok else "BAD ") + want + " <- " + text[:40])
    v, f = check("Great stuff #ad", r, "instagram", brand="Acme")
    ok = v == "WARN" and any(c == "brand" for _, c, _ in f); bad += not ok
    print(("ok  " if ok else "BAD ") + "brand missing -> WARN")
    print("SELFTEST " + ("PASSED" if not bad else "FAILED"))
    return 1 if bad else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post", nargs="?", help="text file with the post")
    ap.add_argument("--rules", help="JSON rules file (same keys as --print-rules)")
    ap.add_argument("--platform", default="default")
    ap.add_argument("--brand", help="brand name that must appear in the text")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--print-rules", action="store_true")
    a = ap.parse_args()
    if a.selftest: sys.exit(selftest())
    if a.print_rules:
        print(json.dumps(DEFAULT_RULES, indent=2)); return
    if not a.post: ap.error("post file required")
    rules = dict(DEFAULT_RULES)
    if a.rules:
        with open(a.rules, encoding="utf-8") as fh: rules.update(json.load(fh))
    with open(a.post, encoding="utf-8") as fh: text = fh.read()
    v, f = check(text, rules, a.platform.lower(), a.brand)
    if a.json: print(json.dumps({"verdict": v, "findings": [dict(level=l, code=c, message=m) for l, c, m in f]}, indent=2))
    else: print(render(v, f))
    sys.exit(0 if v != "FAIL" else 2)

if __name__ == "__main__":
    main()
