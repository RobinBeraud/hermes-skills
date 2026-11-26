#!/usr/bin/env python3
"""Check an SRT or WebVTT subtitle file for readability problems.

Usage:
  python3 srt_check.py FILE [--max-cps 17] [--max-line 42] [--max-lines 2]
                       [--min-dur 1.0] [--max-dur 7.0] [--json]
  python3 srt_check.py --selftest
Standard library only.
"""
import argparse, json, re, sys

TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})")


def to_sec(m):
    h = int(m.group(1) or 0)
    ms = m.group(4).ljust(3, "0")
    return h * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(ms) / 1000


def parse(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        for i, l in enumerate(lines):
            if "-->" in l:
                a, b = l.split("-->", 1)
                ma, mb = TS.search(a), TS.search(b)
                if not (ma and mb):
                    break
                body = [x for x in lines[i + 1:] if x.strip()]
                body = [re.sub(r"<[^>]+>", "", x).strip() for x in body]
                cues.append({"index": len(cues) + 1, "start": to_sec(ma),
                             "end": to_sec(mb), "lines": body})
                break
    return cues


def fmt(t):
    m, s = divmod(t, 60)
    return "%02d:%05.2f" % (m, s)


def check(cues, max_cps=17, max_line=42, max_lines=2, min_dur=1.0, max_dur=7.0):
    issues = []

    def add(c, kind, msg):
        issues.append({"cue": c["index"], "at": fmt(c["start"]), "type": kind, "detail": msg})

    prev = None
    for c in cues:
        dur = c["end"] - c["start"]
        chars = sum(len(l) for l in c["lines"])
        if dur <= 0:
            add(c, "bad-timing", "end is not after start")
            prev = c
            continue
        if not c["lines"]:
            add(c, "empty", "cue has no text")
        cps = chars / dur
        if cps > max_cps:
            add(c, "too-fast", "%.1f chars/sec (limit %s)" % (cps, max_cps))
        if dur < min_dur and chars:
            add(c, "too-short", "%.2fs on screen (min %s)" % (dur, min_dur))
        if dur > max_dur:
            add(c, "too-long", "%.1fs on screen (max %s)" % (dur, max_dur))
        if len(c["lines"]) > max_lines:
            add(c, "too-many-lines", "%d lines (max %d)" % (len(c["lines"]), max_lines))
        for l in c["lines"]:
            if len(l) > max_line:
                add(c, "line-too-long", "%d chars: \"%s\"" % (len(l), l[:50]))
                break
        if re.search(r"\s{2,}", " ".join(c["lines"])):
            add(c, "double-space", "repeated spaces")
        if prev is not None:
            if c["start"] < prev["start"]:
                add(c, "out-of-order", "starts before previous cue")
            elif c["start"] < prev["end"]:
                add(c, "overlap", "starts %.2fs before previous cue ends" % (prev["end"] - c["start"]))
        prev = c
    return issues


SAMPLE = """1
00:00:01,000 --> 00:00:03,000
Hello and welcome back to the channel.

2
00:00:03,000 --> 00:00:03,400
Quick.

3
00:00:03,300 --> 00:00:05,000
This line is intentionally far too long to fit comfortably on one screen line

4
00:00:05,000 --> 00:00:06,000
Short and fine.
"""


def selftest():
    cues = parse(SAMPLE)
    assert len(cues) == 4, len(cues)
    kinds = {i["type"] for i in check(cues)}
    for k in ("too-short", "overlap", "line-too-long", "too-fast"):
        assert k in kinds, (k, kinds)
    vtt = "WEBVTT\n\n00:01.000 --> 00:02.500\nHi there\n"
    assert len(parse(vtt)) == 1 and abs(parse(vtt)[0]["end"] - 2.5) < 1e-6
    assert check(parse(vtt)) == []
    print("selftest OK")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", nargs="?")
    p.add_argument("--max-cps", type=float, default=17)
    p.add_argument("--max-line", type=int, default=42)
    p.add_argument("--max-lines", type=int, default=2)
    p.add_argument("--min-dur", type=float, default=1.0)
    p.add_argument("--max-dur", type=float, default=7.0)
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        p.error("FILE required")
    with open(a.file, encoding="utf-8", errors="replace") as f:
        cues = parse(f.read())
    if not cues:
        print("No cues found. Is this an SRT or WebVTT file?", file=sys.stderr)
        sys.exit(2)
    issues = check(cues, a.max_cps, a.max_line, a.max_lines, a.min_dur, a.max_dur)
    if a.json:
        print(json.dumps({"cues": len(cues), "issues": issues}, indent=2))
        return
    print("%d cues, %d issues" % (len(cues), len(issues)))
    for i in issues:
        print("  cue %d (%s) %s: %s" % (i["cue"], i["at"], i["type"], i["detail"]))
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
