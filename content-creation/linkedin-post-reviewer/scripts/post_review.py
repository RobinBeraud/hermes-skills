#!/usr/bin/env python3
"""Check the structure and readability of a social post (plain text).

Usage:
  post_review.py post.txt            # review a file
  cat post.txt | post_review.py -    # review stdin
  post_review.py --selftest
Options: --hook-chars N (default 140), --json
Only measures things that can be counted. It does not judge quality or predict reach.
"""
import argparse, json, re, sys

CLICHES = ["excited to announce", "thrilled to announce", "humbled", "game changer",
           "game-changer", "unlock", "leverage", "synergy", "deep dive", "in today's fast-paced",
           "agree?", "thoughts?", "let that sink in", "here's the thing"]
CTA_PATTERNS = [r"\bcomment\b", r"\bshare\b", r"\bfollow\b", r"\bsubscribe\b", r"\bdm me\b",
                r"\bclick\b", r"\blink in\b", r"\bsign up\b", r"\bbook\b", r"\bdownload\b",
                r"\btell me\b", r"\bwhat about you\b", r"\breply\b", r"\bwhich one\b", r"\bwhat would you\b"]
URL_RE = re.compile(r"https?://\S+|www\.\S+")
HASHTAG_RE = re.compile(r"(?<!\w)#\w+")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2705]")


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def analyze(text, hook_chars=140):
    text = text.strip()
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    lines = [l for l in text.splitlines() if l.strip()]
    first_line = lines[0].strip() if lines else ""
    words = re.findall(r"[\w'’-]+", URL_RE.sub("", text))
    sents = sentences(URL_RE.sub("", text))
    sent_lens = [len(re.findall(r"[\w'’-]+", s)) for s in sents] or [0]
    longest_par = max((len(re.findall(r"[\w'’-]+", p)) for p in paragraphs), default=0)
    lower = text.lower()
    found_cliches = [c for c in CLICHES if c in lower]
    ctas = [p for p in CTA_PATTERNS if re.search(p, lower)]
    last_par = paragraphs[-1].lower() if paragraphs else ""
    cta_at_end = any(re.search(p, last_par) for p in CTA_PATTERNS) or last_par.strip().endswith("?")
    urls = URL_RE.findall(text)
    hashtags = HASHTAG_RE.findall(text)
    tail = text[-200:]
    hashtags_mid = [h for h in hashtags if h not in tail]
    m = {
        "characters": len(text), "words": len(words), "paragraphs": len(paragraphs),
        "non_empty_lines": len(lines), "first_line": first_line,
        "first_line_chars": len(first_line),
        "avg_sentence_words": round(sum(sent_lens) / len(sent_lens), 1),
        "longest_sentence_words": max(sent_lens),
        "longest_paragraph_words": longest_par,
        "urls": len(urls), "hashtags": len(hashtags), "hashtags_outside_end": len(hashtags_mid),
        "emojis": len(EMOJI_RE.findall(text)),
        "cliches": found_cliches, "cta_words": ctas, "cta_near_end": cta_at_end,
    }
    flags = []
    if m["first_line_chars"] > hook_chars:
        flags.append(f"HOOK: first line is {m['first_line_chars']} chars (> {hook_chars}); the part shown before a 'see more' cut may end mid-thought.")
    if m["first_line_chars"] and m["first_line_chars"] < 15:
        flags.append("HOOK: first line is very short; make sure it still tells the reader why to continue.")
    if m["words"] > 60 and m["paragraphs"] < 3:
        flags.append("LAYOUT: long text in fewer than 3 paragraphs (wall of text).")
    if longest_par > 70:
        flags.append(f"LAYOUT: one paragraph has {longest_par} words; consider splitting.")
    if m["longest_sentence_words"] > 35:
        flags.append(f"READABILITY: longest sentence has {m['longest_sentence_words']} words.")
    if m["avg_sentence_words"] > 22:
        flags.append(f"READABILITY: average sentence length is {m['avg_sentence_words']} words.")
    if not cta_at_end:
        flags.append("CTA: no clear question or call to action in the last paragraph.")
    if len(ctas) > 3:
        flags.append("CTA: many different asks (" + ", ".join(ctas[:5]) + "); pick one.")
    if m["urls"] and m["words"] > 0:
        flags.append("LINK: a URL is in the body; some platforms may show posts with links differently. Consider putting it in a comment or at the end (check your own results).")
    if m["hashtags"] > 5:
        flags.append(f"HASHTAGS: {m['hashtags']} hashtags; few, relevant ones usually read better.")
    if m["hashtags_outside_end"]:
        flags.append("HASHTAGS: some hashtags sit in the middle of the text.")
    if m["emojis"] > 8:
        flags.append(f"EMOJI: {m['emojis']} emojis; check that they help rather than clutter.")
    if found_cliches:
        flags.append("PHRASES: stock phrases found: " + ", ".join(found_cliches))
    m["flags"] = flags
    return m


def render(m):
    out = [f"Characters: {m['characters']} | Words: {m['words']} | Paragraphs: {m['paragraphs']}",
           f"First line ({m['first_line_chars']} chars): {m['first_line']}",
           f"Avg sentence: {m['avg_sentence_words']} words | Longest: {m['longest_sentence_words']} | Longest paragraph: {m['longest_paragraph_words']}",
           f"URLs: {m['urls']} | Hashtags: {m['hashtags']} | Emojis: {m['emojis']}", ""]
    out.append("Flags:" if m["flags"] else "No flags raised.")
    out += [f"- {f}" for f in m["flags"]]
    return "\n".join(out)


def selftest():
    bad = ("I'm excited to announce that after a very long journey of learning many things about the way people "
           "read things online we finally have something to share with all of you today and it is a game changer "
           "for everyone who works in this space https://example.com " + "word " * 80 + "#a #b #c #d #e #f #g")
    m = analyze(bad)
    assert m["urls"] == 1 and m["hashtags"] == 7, m
    assert any(f.startswith("HOOK") for f in m["flags"])
    assert any(f.startswith("LAYOUT") for f in m["flags"])
    assert any("excited to announce" in f for f in m["flags"])
    good = "Stop writing captions last.\n\nI draft them first now.\nThe video follows the caption.\n\nWhich order do you use?"
    g = analyze(good)
    assert g["flags"] == [], g["flags"]
    assert g["paragraphs"] == 3 and g["cta_near_end"]
    assert analyze("")["words"] == 0
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?")
    ap.add_argument("--hook-chars", type=int, default=140)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.path:
        ap.error("give a file path or '-' for stdin")
    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    m = analyze(text, a.hook_chars)
    print(json.dumps(m, indent=2, ensure_ascii=False) if a.json else render(m))


if __name__ == "__main__":
    main()
