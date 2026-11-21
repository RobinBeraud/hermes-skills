#!/usr/bin/env python3
"""Check a UGC creator brief (Markdown or text) for missing sections and vague wording.

Usage:
  brief_check.py BRIEF.md        check a brief file
  brief_check.py --selftest      run built-in tests
Python 3 standard library only.
"""
import re
import sys

SECTIONS = {
    "objective": r"objective|goal|purpose",
    "key messages": r"key message|main message|talking point",
    "do": r"\bdo\b|must include|required",
    "dont": r"don'?t|avoid|do not|must not",
    "deliverables": r"deliverable|format|length|duration|how many",
    "deadline": r"deadline|due date|deliver by|schedule|timeline",
    "usage rights": r"usage right|licen[cs]e|rights|whitelist|paid ads|usage",
    "disclosure": r"disclos|#ad|paid partnership|sponsored|ad label",
    "payment": r"payment|\bfee\b|compensation|gifted",
    "revisions": r"revision|feedback round|changes",
}

VAGUE = [
    "make it pop", "go viral", "be authentic", "feel natural", "as soon as possible",
    "asap", "high quality", "nice vibe", "engaging", "trendy", "short video",
    "soon", "etc", "some", "a few",
]

RIGHTS_DETAILS = {
    "duration of use": r"\b\d+\s*(day|week|month|year)s?\b|perpetual|unlimited",
    "where it may run": r"organic|paid ad|whitelist|website|instagram|tiktok|youtube|email|in-store|social",
}


def heading_text(text):
    heads = re.findall(r"^\s{0,3}#{1,6}\s*(.+)$|^\s*\*\*(.+?)\*\*\s*:?\s*$", text, re.M)
    return [a or b for a, b in heads]


def check(text):
    problems = []
    heads = " | ".join(heading_text(text)).lower()
    low = text.lower()
    for name, pat in SECTIONS.items():
        if not re.search(pat, heads):
            if re.search(pat, low):
                problems.append(("WARN", f"'{name}' is mentioned but has no heading of its own"))
            else:
                problems.append(("MISSING", f"no section about {name}"))
    for phrase in VAGUE:
        if re.search(r"\b" + re.escape(phrase) + r"\b", low):
            problems.append(("VAGUE", f"vague wording: '{phrase}' (say what you mean in concrete terms)"))
    if re.search(SECTIONS["usage rights"], low):
        for name, pat in RIGHTS_DETAILS.items():
            if not re.search(pat, low):
                problems.append(("MISSING", f"usage rights do not state {name}"))
    if re.search(r"\bno\s+(need|requirement)\s+to\s+(disclose|label)|hide the (ad|sponsor)", low):
        problems.append(("BLOCK", "brief asks to hide the commercial relationship: remove it"))
    return problems


def report(problems):
    if not problems:
        return "OK: no problems found"
    return "\n".join(f"[{k}] {m}" for k, m in problems)


GOOD = """# Objective
Show how the Example Mug keeps coffee warm.
## Key messages
- Keeps drinks warm
## Do
- Show the mug in use
## Don't
- Do not compare with other brands
## Deliverables
One 30 second vertical video
## Revisions
Two feedback rounds
## Deadline
Due date: 2027-01-15
## Usage rights
Organic posts on Instagram and TikTok for 3 months
## Disclosure
Add #ad and the platform paid partnership label
## Payment
Fee: 200 EUR, paid within 30 days
"""


def selftest():
    assert report(check(GOOD)).startswith("OK"), report(check(GOOD))
    bad = "# Brief\nMake it pop and go viral. Usage: forever.\nNo need to disclose."
    out = report(check(bad))
    assert "MISSING" in out and "VAGUE" in out and "BLOCK" in out, out
    print("selftest passed")


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        selftest()
        return 0
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(argv) == 2 else 2
    with open(argv[1], encoding="utf-8") as f:
        text = f.read()
    probs = check(text)
    print(report(probs))
    return 1 if any(k in ("MISSING", "BLOCK") for k, _ in probs) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
