#!/usr/bin/env python3
"""Build a 'source brief' from an article, transcript (.srt/.vtt) or notes file.

Output (Markdown or JSON): size, voice fingerprint, quotable lines, key
sentences, facts (numbers/links) that must be preserved when repurposing.
Python 3 standard library only. No network.
"""
import argparse, json, re, sys
from collections import Counter

STOP = set("""a an and are as at be but by for from has have he her his i if in into is it its
me my not of on or our she so that the their them then there these they this to up us was we were
what when which who will with you your just like also can do does did than too very about all any
how out one more some such only over""".split())
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
TS = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?[.,]\d{3}\s*-->.*$")


def clean(text):
    """Strip SRT/VTT numbering, timestamps and tags; keep spoken text."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.upper() == "WEBVTT" or s.isdigit() or TS.match(s):
            continue
        if s.startswith(("NOTE", "Kind:", "Language:")) or re.match(r"^#{1,6}\s", s):
            continue
        out.append(re.sub(r"<[^>]+>", "", s))
    return "\n".join(out)


def sentences(text):
    flat = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", flat)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def words(s):
    return re.findall(r"[A-Za-z0-9']+", s.lower())


def analyse(text):
    body = clean(text)
    sents = [x for x in sentences(body) if "http" not in x]
    allw = words(body)
    n = max(len(allw), 1)
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    lens = [len(words(s)) for s in sents] or [0]
    fp = {
        "words": len(allw),
        "read_minutes": round(len(allw) / 230, 1),
        "sentences": len(sents),
        "avg_sentence_words": round(sum(lens) / len(lens), 1),
        "short_sentence_share": round(sum(1 for l in lens if l <= 8) / len(lens), 2),
        "question_share": round(sum(1 for s in sents if s.endswith("?")) / max(len(sents), 1), 2),
        "exclamation_share": round(sum(1 for s in sents if s.endswith("!")) / max(len(sents), 1), 2),
        "first_person_per_100w": round(100 * sum(w in ("i", "my", "me", "we", "our") for w in allw) / n, 1),
        "you_per_100w": round(100 * sum(w in ("you", "your") for w in allw) / n, 1),
        "contractions_per_100w": round(100 * sum("'" in w for w in allw) / n, 1),
        "emoji_count": len(EMOJI.findall(body)),
        "paragraphs": len(paras),
    }
    tone = []
    tone.append("short punchy sentences" if fp["avg_sentence_words"] < 14 else "longer, explanatory sentences")
    tone.append("speaks to the reader directly ('you')" if fp["you_per_100w"] >= 1.5 else "mostly third-person / neutral")
    tone.append("personal ('I', 'we')" if fp["first_person_per_100w"] >= 1.5 else "impersonal")
    tone.append("casual (contractions)" if fp["contractions_per_100w"] >= 1.0 else "formal (few contractions)")
    fp["voice_summary"] = tone

    # key sentences: score by frequency of non-stop words, favour mid-length
    freq = Counter(w for w in allw if w not in STOP and len(w) > 3)
    scored = []
    for i, s in enumerate(sents):
        ws = [w for w in words(s) if w not in STOP and len(w) > 3]
        if not ws:
            continue
        L = len(words(s))
        score = sum(freq[w] for w in set(ws)) / (len(set(ws)) ** 0.5)
        if 8 <= L <= 30:
            score *= 1.2
        scored.append((score, i, s))
    top = sorted(scored, reverse=True)[:8]
    key = [s for _, _, s in sorted(top, key=lambda t: t[1])]

    # quotable lines: short, self-contained, no leading connector
    bad = re.compile(r"^(and|but|so|because|which|then|or)\b", re.I)
    quotes = [s for s in sents if 7 <= len(words(s)) <= 22 and not bad.match(s)
              and not re.search(r"\b(this|that|it|they)\b", s.split()[0].lower())]
    quotes = sorted(quotes, key=lambda s: -(("?" in s) + bool(re.search(r"\d", s)) + 0.5 * bool(re.search(r"\b(never|always|stop|start|why|because|instead|mistake|truth)\b", s, re.I))))[:8]

    facts = sorted(set(re.findall(r"\b\d[\d,.]*\s?(?:%|percent|x|k|M|hours?|minutes?|days?|weeks?|years?|euros?|dollars?|USD|EUR)?", body)))
    facts = [f.strip() for f in facts if f.strip() and not f.strip().isdigit() or len(f.strip()) >= 3][:25]
    links = sorted(set(re.findall(r"https?://[^\s)>\]\"']+", text)))
    heads = [l.strip("# ").strip() for l in text.splitlines() if re.match(r"^#{1,4}\s+\S", l)]
    return {"fingerprint": fp, "headings": heads, "key_sentences": key,
            "quotable_lines": quotes, "facts_to_preserve": facts, "links": links}


def to_md(r):
    fp = r["fingerprint"]
    o = ["# Source brief", "", "## Voice fingerprint"]
    o += [f"- {k}: {v}" for k, v in fp.items() if k != "voice_summary"]
    o += ["- reads as: " + "; ".join(fp["voice_summary"]), ""]
    for title, key in (("Headings", "headings"), ("Key sentences (core ideas)", "key_sentences"),
                       ("Quotable lines (verbatim, reuse as-is)", "quotable_lines"),
                       ("Facts to preserve exactly", "facts_to_preserve"), ("Links in source", "links")):
        o.append(f"## {title}")
        o += [f"- {x}" for x in r[key]] or ["- (none found)"]
        o.append("")
    return "\n".join(o)


def selftest():
    sample = ("# Why I stopped batch filming\n\nI used to film ten videos in one Saturday. It felt efficient! "
              "But my energy was gone by video four, and you could see it on screen.\n\n"
              "Here's what changed: I film two videos, then I stop. Why does that work? Because attention is the real budget. "
              "After the switch, editing took 3 hours instead of 6 hours. Never trade energy for volume. "
              "Read more at https://example.com/post today.")
    r = analyse(sample)
    assert r["fingerprint"]["words"] > 50
    assert r["fingerprint"]["question_share"] > 0
    assert any("3 hours" in f for f in r["facts_to_preserve"]), r["facts_to_preserve"]
    assert r["links"] == ["https://example.com/post"]
    assert r["headings"] == ["Why I stopped batch filming"]
    srt = "1\n00:00:01,000 --> 00:00:03,000\nHello there, friends.\n\n2\n00:00:03,500 --> 00:00:06,000\nToday we talk about editing.\n"
    assert clean(srt) == "Hello there, friends.\nToday we talk about editing."
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", nargs="?", help="text, markdown, .srt or .vtt file (or - for stdin)")
    ap.add_argument("--json", action="store_true", help="JSON output instead of Markdown")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("file required")
    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8", errors="replace").read()
    r = analyse(text)
    print(json.dumps(r, indent=2, ensure_ascii=False) if a.json else to_md(r))


if __name__ == "__main__":
    main()
