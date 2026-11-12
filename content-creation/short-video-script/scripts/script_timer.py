#!/usr/bin/env python3
"""Check the timing of a short-video script and print caption chunks.

Script file format (plain text, one block per line):
    HOOK: spoken words for the first seconds
    BEAT: spoken words for a middle part
    TURN: spoken words for the twist / payoff
    CTA: spoken call to action
Optional on any line: text in [square brackets] is a visual note and is NOT spoken.
Lines starting with # and blank lines are ignored.
"""
import argparse
import re
import sys

LABELS = ("HOOK", "BEAT", "TURN", "CTA")
LINE_RE = re.compile(r"^\s*(HOOK|BEAT|TURN|CTA)\s*:\s*(.*)$", re.I)


def parse(text):
    blocks = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            raise ValueError("line %d: expected HOOK:/BEAT:/TURN:/CTA: prefix, got: %r" % (n, line[:40]))
        visual = re.findall(r"\[([^\]]*)\]", m.group(2))
        spoken = re.sub(r"\[[^\]]*\]", " ", m.group(2))
        words = spoken.split()
        blocks.append({"label": m.group(1).upper(), "words": words, "visual": visual, "line": n})
    return blocks


def fmt(t):
    ms = int(round(t * 1000))
    return "%02d:%02d.%03d" % (ms // 60000, (ms // 1000) % 60, ms % 1000)


def analyse(blocks, wps, target, hook_max_s, chunk):
    problems = []
    if not blocks:
        return {"problems": ["script is empty"], "total": 0.0, "captions": []}
    labels = [b["label"] for b in blocks]
    if labels[0] != "HOOK":
        problems.append("script should start with a HOOK line")
    if labels.count("HOOK") != 1:
        problems.append("expected exactly one HOOK, found %d" % labels.count("HOOK"))
    if "CTA" not in labels:
        problems.append("no CTA line (one clear next step for the viewer)")
    elif labels[-1] != "CTA":
        problems.append("CTA is not the last line")
    t = 0.0
    caps = []
    for b in blocks:
        b["start"] = t
        b["dur"] = len(b["words"]) / wps
        t += b["dur"]
        b["end"] = t
        if b["label"] == "HOOK" and b["dur"] > hook_max_s:
            problems.append("hook takes about %.1fs to say, limit is %.1fs (%d words)" % (b["dur"], hook_max_s, len(b["words"])))
        if not b["words"]:
            problems.append("line %d (%s) has no spoken words" % (b["line"], b["label"]))
        if not b["visual"]:
            problems.append("line %d (%s) has no [visual note]" % (b["line"], b["label"]))
        w = b["words"]
        for i in range(0, len(w), chunk):
            part = w[i:i + chunk]
            s = b["start"] + i / wps
            e = b["start"] + (i + len(part)) / wps
            caps.append((s, e, " ".join(part)))
    if t > target:
        problems.append("total about %.1fs, over the %.0fs target" % (t, target))
    return {"problems": problems, "total": t, "captions": caps}


def render(blocks, res, wps, target):
    out = ["Estimated speaking pace: %.2f words/second" % wps]
    for b in blocks:
        out.append("%s-%s  %-4s %3d words  %.1fs" % (fmt(b["start"])[:8], fmt(b["end"])[:8], b["label"], len(b["words"]), b["dur"]))
    out.append("TOTAL: %.1fs (target %.0fs)" % (res["total"], target))
    out.append("")
    out.append("Caption chunks:")
    for i, (s, e, txt) in enumerate(res["captions"], 1):
        out.append("%d\n%s --> %s\n%s" % (i, fmt(s), fmt(e), txt))
    out.append("")
    if res["problems"]:
        out.append("PROBLEMS:")
        out.extend("- " + p for p in res["problems"])
    else:
        out.append("No problems found.")
    return "\n".join(out)


SAMPLE = """# sample
HOOK: You are editing your videos in the wrong order. [close-up, text on screen: WRONG ORDER]
BEAT: Most people cut the footage first and add sound last. [screen recording of a timeline]
BEAT: Start with the voice track, then cut the picture to match it. [split screen]
TURN: The video suddenly feels faster without any new effects. [before/after]
CTA: Try it on your next clip and tell me what changed. [face to camera]
"""


def selftest():
    blocks = parse(SAMPLE)
    assert [b["label"] for b in blocks] == ["HOOK", "BEAT", "BEAT", "TURN", "CTA"]
    assert "WRONG" not in " ".join(blocks[0]["words"])
    res = analyse(blocks, 2.5, 60, 4.0, 4)
    assert not res["problems"], res["problems"]
    assert 0 < res["total"] < 60
    assert res["captions"][0][0] == 0.0
    bad = parse("BEAT: one two three [x]\nHOOK: a b c d e f g h i j k l m n o p [y]")
    r2 = analyse(bad, 2.5, 3, 3.0, 4)
    txt = " ".join(r2["problems"])
    assert "start with a HOOK" in txt and "no CTA" in txt and "hook takes" in txt and "over the" in txt, txt
    try:
        parse("hello")
    except ValueError:
        pass
    else:
        raise AssertionError("bad line accepted")
    print("selftest OK")


def main():
    p = argparse.ArgumentParser(description="Time a short-video script and print caption chunks.")
    p.add_argument("file", nargs="?", help="script file (HOOK:/BEAT:/TURN:/CTA: lines); '-' for stdin")
    p.add_argument("--wps", type=float, default=2.5, help="speaking pace in words per second (default 2.5)")
    p.add_argument("--target", type=float, default=45, help="maximum total seconds (default 45)")
    p.add_argument("--hook-max", type=float, default=3.0, help="maximum hook seconds (default 3)")
    p.add_argument("--chunk", type=int, default=4, help="words per caption chunk (default 4)")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.file:
        p.error("file required (or --selftest)")
    if a.wps <= 0 or a.chunk < 1:
        p.error("--wps must be > 0 and --chunk >= 1")
    text = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    try:
        blocks = parse(text)
    except ValueError as e:
        print("ERROR:", e, file=sys.stderr)
        return 2
    res = analyse(blocks, a.wps, a.target, a.hook_max, a.chunk)
    if not blocks:
        print("ERROR: script is empty", file=sys.stderr)
        return 2
    print(render(blocks, res, a.wps, a.target))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
