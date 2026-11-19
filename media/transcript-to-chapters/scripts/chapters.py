#!/usr/bin/env python3
"""Turn an SRT/VTT transcript into chapter candidates, keywords and quote candidates.

Standard library only. The script finds WHERE topics shift and WHAT words dominate
each part; the agent then writes the human titles and summaries.

Usage:
  chapters.py FILE [--chapters N] [--min-seconds S] [--format md|json]
  chapters.py --selftest
"""
import argparse, json, math, re, sys
from collections import Counter

STOP = set("""a an the and or but if so of to in on at for with from by as is are was were be been being it its this that
these those i you he she we they me my your our their them his her not no yes do does did done have has had will would can
could should just like really very about into out up down over then than there here what which who whom when where why how
all any some more most other such only own same too also get got going go gone know think mean okay ok well right yeah um uh
oh now one two thing things way want need let us lets say said see look make made much many even still back because while
le la les un une des et ou mais de du en dans sur pour avec par est sont a au aux ce cette ces je tu il elle nous vous ils
elles ne pas que qui quoi donc alors voila ca c' d' l' j' n' s' qu'""".split())

TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})")

def to_sec(m):
    h, mi, s, ms = m.groups()
    return int(h or 0) * 3600 + int(mi) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000

def parse(text):
    """Return list of (start, end, text) from SRT or VTT content."""
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        for i, l in enumerate(lines):
            if "-->" in l:
                a, b = l.split("-->", 1)
                ma, mb = TS.search(a), TS.search(b)
                if not (ma and mb):
                    break
                body = " ".join(lines[i + 1:])
                body = re.sub(r"<[^>]+>", "", body)          # VTT tags
                body = re.sub(r"\{[^}]*\}", "", body)         # SRT style tags
                body = re.sub(r"\s+", " ", body).strip()
                if body:
                    cues.append((to_sec(ma), to_sec(mb), body))
                break
    # drop consecutive duplicated lines (common in auto-captions)
    out = []
    for c in cues:
        if out and out[-1][2] == c[2]:
            out[-1] = (out[-1][0], c[1], c[2])
        else:
            out.append(c)
    return out

def fmt(sec):
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def words(t):
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ']{3,}", t.lower()) if w.strip("'") not in STOP]

def cosine(a, b):
    if not a or not b:
        return 0.0
    num = sum(a[k] * b.get(k, 0) for k in a)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0

def blocks(cues, size=30.0):
    """Group cues into ~size-second blocks."""
    out, cur, start = [], [], None
    for s, e, t in cues:
        if start is None:
            start = s
        cur.append((s, e, t))
        if e - start >= size:
            out.append(cur); cur, start = [], None
    if cur:
        out.append(cur)
    return out

def suggest(cues, n=None, min_seconds=60.0):
    if not cues:
        return []
    total = cues[-1][1]
    bl = blocks(cues)
    counts = [Counter(words(" ".join(t for _, _, t in b))) for b in bl]
    starts = [b[0][0] for b in bl]
    # boundary score between block i-1 and i: low similarity of the neighbourhoods = topic shift
    scores = []
    for i in range(1, len(bl)):
        left = sum((counts[j] for j in range(max(0, i - 3), i)), Counter())
        right = sum((counts[j] for j in range(i, min(len(bl), i + 3))), Counter())
        gap = bl[i][0][0] - bl[i - 1][-1][1]
        scores.append((cosine(left, right) - min(gap, 5) * 0.02, i))
    if n is None:
        n = max(3, min(12, round(total / 300)))   # roughly one chapter per 5 minutes
    chosen = []
    for sc, i in sorted(scores):
        t = starts[i]
        if t < min_seconds or total - t < min_seconds:
            continue
        if all(abs(t - c) >= min_seconds for c in chosen):
            chosen.append(t)
        if len(chosen) >= n - 1:
            break
    bounds = [0.0] + sorted(chosen)
    chapters = []
    for k, b in enumerate(bounds):
        end = bounds[k + 1] if k + 1 < len(bounds) else total
        part = [c for c in cues if b <= c[0] < end]
        text = " ".join(c[2] for c in part)
        kw = [w for w, _ in Counter(words(text)).most_common(6)]
        chapters.append({"start": b, "label": fmt(b), "end": end, "keywords": kw,
                         "opening": text[:160]})
    return chapters

def quotes(cues, limit=8):
    """Sentence-like candidates of 8-28 words. The agent must still judge and check them."""
    text = [(s, t) for s, _, t in cues]
    cands = []
    for s, t in text:
        for sent in re.split(r"(?<=[.!?])\s+", t):
            n = len(sent.split())
            if 8 <= n <= 28:
                w = words(sent)
                cands.append((len(set(w)) / max(n, 1) + (0.2 if re.search(r"\d|\?|!", sent) else 0), s, sent))
    cands.sort(reverse=True)
    seen, out = set(), []
    for sc, s, sent in cands:
        if sent in seen:
            continue
        seen.add(sent); out.append({"at": fmt(s), "text": sent})
        if len(out) >= limit:
            break
    return out

def youtube_ok(chapters):
    p = []
    if len(chapters) < 3: p.append("YouTube needs at least 3 chapters")
    if chapters and chapters[0]["start"] != 0: p.append("first chapter must start at 0:00")
    for a, b in zip(chapters, chapters[1:]):
        if b["start"] - a["start"] < 10: p.append(f"chapter at {a['label']} is shorter than 10 seconds")
    return p

SAMPLE = """1
00:00:00,000 --> 00:00:08,000
Welcome back. Today we talk about baking sourdough bread at home, flour and starter first.

2
00:00:08,000 --> 00:00:40,000
A healthy starter doubles in about six hours. Feed the starter with flour and water every day. The starter smells sweet when it is ready.

3
00:00:40,000 --> 00:01:20,000
Use the starter when it floats. Flour choice matters: a strong bread flour gives more structure. Flour and starter ratio is the base.

4
00:01:20,000 --> 00:02:10,000
Now mixing the dough. Mix flour, water and starter, then rest the dough for thirty minutes. Folding the dough builds strength.

5
00:02:10,000 --> 00:03:00,000
Fold the dough every thirty minutes, four times. The dough should feel smooth. Dough that tears needs more rest.

6
00:03:00,000 --> 00:03:50,000
Baking time. Preheat the oven with a heavy pot inside. The oven must be very hot before the loaf goes in.

7
00:03:50,000 --> 00:04:40,000
Bake the loaf covered, then uncover the loaf for browning. Crust color tells you when the loaf is done. Cool the loaf before slicing!

8
00:04:40,000 --> 00:05:30,000
Storage tips: keep the loaf in a cloth bag, freeze slices, and toast slices from frozen. Thanks for watching, see you next week.
"""

def selftest():
    cues = parse(SAMPLE)
    assert len(cues) == 8, len(cues)
    vtt = "WEBVTT\n\n00:01.000 --> 00:03.500\n<c>Hello there</c>\n\n00:04.000 --> 00:06.000\nSecond line"
    v = parse(vtt)
    assert len(v) == 2 and v[0][2] == "Hello there" and v[1][0] == 4.0, v
    ch = suggest(cues, n=4, min_seconds=45)
    assert ch[0]["start"] == 0 and len(ch) >= 3, ch
    assert not youtube_ok(ch), youtube_ok(ch)
    assert fmt(3725) == "1:02:05" and fmt(65) == "1:05"
    q = quotes(cues)
    assert q and all(8 <= len(x["text"].split()) <= 28 for x in q)
    print("selftest OK:", [c["label"] for c in ch])

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--chapters", type=int, help="target number of chapters (default: about one per 5 min)")
    ap.add_argument("--min-seconds", type=float, default=60.0, help="minimum chapter length (default 60)")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("give a transcript file or --selftest")
    cues = parse(open(a.file, encoding="utf-8", errors="replace").read())
    if not cues:
        sys.exit("No timestamped cues found. Is this an SRT or VTT file?")
    ch = suggest(cues, a.chapters, a.min_seconds)
    qs = quotes(cues)
    problems = youtube_ok(ch)
    if a.format == "json":
        print(json.dumps({"duration": cues[-1][1], "chapters": ch, "quotes": qs, "youtube_problems": problems}, ensure_ascii=False, indent=2))
        return
    print(f"Transcript length: {fmt(cues[-1][1])}  |  cues: {len(cues)}\n\n## Chapter candidates (titles to be written by the agent)")
    for c in ch:
        print(f"- {c['label']}  keywords: {', '.join(c['keywords'])}\n    opens with: {c['opening']}")
    print("\n## Quote candidates (verify wording against the transcript before use)")
    for q in qs:
        print(f"- [{q['at']}] {q['text']}")
    print("\n## YouTube rules check:", "OK" if not problems else "; ".join(problems))

if __name__ == "__main__":
    main()
