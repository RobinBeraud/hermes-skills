#!/usr/bin/env python3
"""Check newsletter subject lines against explicit, readable rules.

Input: a text file (one subject per line) or --subject arguments.
Output: a table or JSON with warnings per subject. Standard library only.
The rules are plain heuristics, not measured performance data.
"""
import argparse
import json
import re
import sys

SHOUTY_PHRASES = [
    "act now", "buy now", "100% free", "risk free", "no risk", "guaranteed",
    "make money", "earn cash", "winner", "congratulations", "click here",
    "once in a lifetime", "limited time only", "urgent", "miracle",
]
FAKE_THREAD = re.compile(r"^\s*(re|fwd?|fw)\s*:", re.I)
URGENCY = re.compile(r"\b(last chance|final hours?|ends tonight|ends today|hurry|expires)\b", re.I)
DEADLINE = re.compile(r"\b(\d{1,2}[:h]\d{2}|\d{1,2}(st|nd|rd|th)?\s+(of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|(mon|tues?|wednes|thurs?|fri|satur|sun)day|midnight|\d{4}-\d{2}-\d{2})\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
GENERIC = {"newsletter", "weekly update", "update", "news", "hello", "hi", "monthly newsletter", "weekly newsletter"}


def analyse(subject, max_len=60, min_len=15):
    s = subject.strip()
    warnings = []
    n = len(s)
    if n == 0:
        return {"subject": s, "length": 0, "warnings": ["empty"]}
    if n > max_len:
        warnings.append(f"long: {n} chars, may be cut off on phones (limit used: {max_len})")
    if n < min_len:
        warnings.append(f"short: {n} chars, may not say what the email is about (minimum used: {min_len})")
    letters = [c for c in s if c.isalpha()]
    words = re.findall(r"[A-Za-z]{3,}", s)
    caps_words = [w for w in words if w.isupper()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.5 and len(words) > 1:
        warnings.append("mostly capital letters")
    elif len(caps_words) >= 2:
        warnings.append("several ALL-CAPS words: " + ", ".join(caps_words))
    if re.search(r"[!?]{2,}", s) or s.count("!") > 1:
        warnings.append("repeated ! or ?")
    low = s.lower()
    hits = [p for p in SHOUTY_PHRASES if p in low]
    if hits:
        warnings.append("pushy phrases: " + ", ".join(hits))
    if FAKE_THREAD.match(s):
        warnings.append("starts with Re:/Fwd: which fakes an existing conversation (misleading)")
    if URGENCY.search(s) and not DEADLINE.search(s):
        warnings.append("urgency claim without a real date or time: only use if the deadline is true, and name it")
    emojis = EMOJI.findall(s)
    if len(emojis) > 2:
        warnings.append(f"{len(emojis)} emojis, probably too many")
    if low.strip(" .!") in GENERIC:
        warnings.append("generic: says nothing about this issue's content")
    return {"subject": s, "length": n, "warnings": warnings}


def find_duplicates(subjects):
    seen, dups = {}, []
    for i, s in enumerate(subjects):
        key = re.sub(r"\W+", " ", s.lower()).strip()
        if key in seen:
            dups.append((seen[key] + 1, i + 1))
        else:
            seen[key] = i
    return dups


def load(args):
    items = list(args.subject or [])
    if args.file:
        src = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")
        with src:
            items += [l.strip() for l in src if l.strip() and not l.lstrip().startswith("#")]
    return items


def selftest():
    r = analyse("FREE GIFT!!! Click here NOW")
    assert any("capital" in w or "ALL-CAPS" in w for w in r["warnings"]), r
    assert any("repeated" in w for w in r["warnings"]), r
    assert any("pushy" in w for w in r["warnings"]), r
    assert any("Re:" in w for w in analyse("Re: your order")["warnings"])
    assert any("urgency" in w for w in analyse("Last chance to join the workshop")["warnings"])
    assert not any("urgency" in w for w in analyse("Last chance to join: closes Friday 18:00")["warnings"])
    assert analyse("Three edits that made my intro shorter")["warnings"] == []
    assert any("generic" in w for w in analyse("Newsletter")["warnings"])
    assert find_duplicates(["A b", "x", "a  B!"]) == [(1, 3)]
    print("selftest OK")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", nargs="?", help="text file, one subject per line ('-' for stdin)")
    p.add_argument("--subject", action="append", help="a subject line (repeatable)")
    p.add_argument("--max-len", type=int, default=60)
    p.add_argument("--min-len", type=int, default=15)
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    subjects = load(a)
    if not subjects:
        p.error("give a file or at least one --subject")
    results = [analyse(s, a.max_len, a.min_len) for s in subjects]
    dups = find_duplicates(subjects)
    if a.json:
        print(json.dumps({"results": results, "duplicates": dups}, indent=2, ensure_ascii=False))
        return
    for i, r in enumerate(results, 1):
        status = "OK  " if not r["warnings"] else "WARN"
        print(f"{i}. [{status}] ({r['length']} chars) {r['subject']}")
        for w in r["warnings"]:
            print(f"     - {w}")
    for a_, b_ in dups:
        print(f"Duplicate: lines {a_} and {b_} are the same apart from case/punctuation")
    print(f"{sum(1 for r in results if not r['warnings'])}/{len(results)} without warnings")


if __name__ == "__main__":
    main()
