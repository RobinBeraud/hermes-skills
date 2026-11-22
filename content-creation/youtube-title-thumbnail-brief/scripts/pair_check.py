#!/usr/bin/env python3
"""Check video title + thumbnail pairs for length, readability and honesty.

Input: a text file, one candidate per line:
    title | thumbnail text | visual description
Lines starting with # and blank lines are ignored.

Usage:
    python3 pair_check.py candidates.txt [--max-title 60] [--max-thumb-words 4]
    python3 pair_check.py --selftest
Exit code: 1 if any [BLOCK] or [FIX] line is printed, otherwise 0.
"""
import argparse
import re
import sys
import tempfile
import os

CLICKBAIT = [
    "you won't believe", "you wont believe", "shocking", "gone wrong",
    "doctors hate", "this one trick", "insane", "mind-blowing", "mind blowing",
    "will blow your mind", "secret they don't want", "guaranteed",
    "100% works", "get rich", "exposed",
]
FILLER = {"the", "a", "an", "to", "of", "and", "in", "on", "for", "is", "my", "your", "how", "i", "you", "with"}


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def check_line(n, line, max_title, max_thumb_words):
    out = []
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3 or not all(parts[:3]):
        return [f"[FIX] line {n}: expected 'title | thumbnail text | visual', got {len(parts)} part(s) or an empty one"]
    title, thumb, visual = parts[0], parts[1], " | ".join(parts[2:])
    tl = title.lower()

    if len(title) > max_title:
        out.append(f"[FIX] line {n}: title is {len(title)} characters (limit set to {max_title}); the end may be cut off in lists")
    if len(title) < 15:
        out.append(f"[WARN] line {n}: title is very short ({len(title)} characters); say what the viewer gets")
    letters = [c for c in title if c.isalpha()]
    if len(letters) > 8 and sum(c.isupper() for c in letters) / len(letters) > 0.6:
        out.append(f"[WARN] line {n}: title is mostly capital letters; harder to read")
    if title.count("!") > 1 or "?!" in title:
        out.append(f"[WARN] line {n}: too many exclamation marks")
    for phrase in CLICKBAIT:
        if phrase in tl or phrase in thumb.lower():
            out.append(f"[BLOCK] line {n}: promise-style wording '{phrase}'; only promise what the video really shows")

    tw = words(thumb)
    if len(tw) > max_thumb_words:
        out.append(f"[FIX] line {n}: thumbnail text has {len(tw)} words (limit {max_thumb_words}); it must be readable at small size")
    title_words = {w for w in words(title) if w not in FILLER}
    thumb_words = {w for w in tw if w not in FILLER}
    if thumb_words and thumb_words <= title_words:
        out.append(f"[FIX] line {n}: thumbnail text only repeats the title; add a new angle (a result, a question, a contrast)")
    if len(words(visual)) < 4:
        out.append(f"[FIX] line {n}: visual description is too short to brief a designer (who or what is shown, where, which expression)")
    return out


def check_file(path, max_title, max_thumb_words):
    problems = []
    seen = {}
    count = 0
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            count += 1
            problems += check_line(n, line, max_title, max_thumb_words)
            key = " ".join(words(line.split("|")[0]))
            if key in seen:
                problems.append(f"[FIX] line {n}: same title as line {seen[key]}")
            seen[key] = n
    if count == 0:
        problems.append("[FIX] no candidates found in the file")
    return problems


def selftest():
    sample = (
        "# demo\n"
        "I tested 5 free editing apps on a phone | Which is best? | Creator holding phone, surprised face, five app icons behind\n"
        "SHOCKING: you won't believe this editing trick!! | WOW | face\n"
        "How to edit a video on your phone | Edit a video on phone | Phone screen close-up\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write(sample)
        path = fh.name
    try:
        res = check_file(path, 60, 4)
    finally:
        os.remove(path)
    text = "\n".join(res)
    assert not any("line 2" in r for r in res), text
    assert any(r.startswith("[BLOCK] line 3") for r in res), text
    assert any("line 4" in r and "only repeats the title" in r for r in res), text
    print(text)
    print("SELFTEST OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--max-title", type=int, default=60)
    ap.add_argument("--max-thumb-words", type=int, default=4)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.file:
        ap.error("give a candidates file or --selftest")
    problems = check_file(a.file, a.max_title, a.max_thumb_words)
    if not problems:
        print("OK: no problems found")
        return 0
    print("\n".join(problems))
    return 1 if any(p.startswith(("[BLOCK]", "[FIX]")) for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main())
