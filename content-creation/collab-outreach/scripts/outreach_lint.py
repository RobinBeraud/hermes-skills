#!/usr/bin/env python3
"""Lint a batch of collaboration outreach drafts (stdlib only).

Input: a CSV with columns: recipient, message, specific_detail
  - recipient: a fictional or real label for who the message is for
  - message: the drafted message text
  - specific_detail: the concrete thing about the recipient's work that the
    message is supposed to mention (e.g. a video title, a post topic)

Checks per message:
  - the specific_detail actually appears in the message
  - the message is not too long (default max 120 words)
  - no empty-flattery or pressure phrases
  - it contains exactly one clear ask (a question mark count of 1 or 2)
  - it states what the sender offers (word "offer", "share", "send", "swap", ...)
  - it gives an easy way out ("no worries", "no pressure", "feel free to pass")
Across the batch:
  - flags pairs of messages that are too similar (copy-paste feel)

Usage:
  outreach_lint.py drafts.csv [--max-words 120] [--similarity 0.6]
  outreach_lint.py --selftest
"""
import argparse
import csv
import re
import sys

FLATTERY = [
    "huge fan", "big fan", "love your content", "love what you do",
    "amazing content", "you are an inspiration", "you're an inspiration",
    "i've been following you for years", "your content is incredible",
]
PRESSURE = [
    "act now", "last chance", "don't miss", "limited time", "you won't regret",
    "once in a lifetime", "guaranteed", "go viral",
]
OFFER_WORDS = ["offer", "share", "send", "swap", "trade", "feature", "mention",
               "co-create", "guest", "invite", "introduce", "give", "provide"]
EXIT_PHRASES = ["no worries", "no pressure", "feel free to pass", "totally fine if",
                "if it's not a fit", "if it is not a fit", "happy to drop it",
                "no hard feelings"]


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def jaccard(a, b):
    sa, sb = set(words(a)), set(words(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def lint_message(msg, detail, max_words):
    issues = []
    low = msg.lower()
    if not detail.strip():
        issues.append("no specific_detail provided: the message cannot be personal")
    elif detail.strip().lower() not in low:
        issues.append("specific detail not mentioned in the message")
    n = len(words(msg))
    if n > max_words:
        issues.append(f"too long ({n} words, max {max_words})")
    for p in FLATTERY:
        if p in low:
            issues.append(f"generic flattery: '{p}'")
    for p in PRESSURE:
        if p in low:
            issues.append(f"pressure/hype phrase: '{p}'")
    q = msg.count("?")
    if q == 0:
        issues.append("no question: the ask is unclear")
    elif q > 2:
        issues.append(f"{q} questions: keep a single clear ask")
    if not any(w in low for w in OFFER_WORDS):
        issues.append("no visible offer: what does the recipient get?")
    if not any(p in low for p in EXIT_PHRASES):
        issues.append("no easy way out (e.g. 'no pressure if it's not a fit')")
    return issues


def lint_rows(rows, max_words=120, similarity=0.6):
    report = []
    for r in rows:
        report.append((r["recipient"], lint_message(r["message"], r.get("specific_detail", ""), max_words)))
    sims = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            s = jaccard(rows[i]["message"], rows[j]["message"])
            if s >= similarity:
                sims.append((rows[i]["recipient"], rows[j]["recipient"], s))
    return report, sims


def print_report(report, sims):
    bad = 0
    for who, issues in report:
        if issues:
            bad += 1
            print(f"[FIX] {who}")
            for i in issues:
                print(f"   - {i}")
        else:
            print(f"[OK]  {who}")
    for a, b, s in sims:
        print(f"[SIMILAR] {a} <-> {b}: {s:.0%} identical vocabulary, rewrite one")
    print(f"\n{len(report)} messages, {bad} need fixes, {len(sims)} similar pairs")
    return bad + len(sims)


def selftest():
    good = ("Hi Alice, your video 'Sourdough for Beginners' fixed my starter problem. "
            "I run a small baking newsletter and can share your recipe with my readers, "
            "with a link back. Would a short guest feature work for you? "
            "No pressure at all if it's not a fit.")
    bad = ("Hi, huge fan! Love your content, you will go viral with me, last chance "
           "to collaborate now. Let's do it. Reply asap?? Really??? Yes?")
    d, spec = "Sourdough for Beginners", "Sourdough for Beginners"
    assert lint_message(good, spec, 120) == [], lint_message(good, spec, 120)
    issues = lint_message(bad, spec, 120)
    assert any("specific detail" in i for i in issues)
    assert any("flattery" in i for i in issues)
    assert any("pressure" in i for i in issues)
    assert any("questions" in i for i in issues)
    assert any("offer" in i for i in issues)
    assert any("way out" in i for i in issues)
    rows = [{"recipient": "A", "message": good, "specific_detail": spec},
            {"recipient": "B", "message": good.replace("Alice", "Bob"), "specific_detail": spec}]
    _, sims = lint_rows(rows)
    assert sims, "similar messages should be flagged"
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description="Lint collaboration outreach drafts")
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--max-words", type=int, default=120)
    ap.add_argument("--similarity", type=float, default=0.6)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.csv:
        ap.error("csv path required (or --selftest)")
    with open(a.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    need = {"recipient", "message"}
    if not rows or not need <= set(rows[0].keys()):
        print("CSV needs columns: recipient, message, specific_detail", file=sys.stderr)
        return 2
    report, sims = lint_rows(rows, a.max_words, a.similarity)
    return 1 if print_report(report, sims) else 0


if __name__ == "__main__":
    sys.exit(main())
