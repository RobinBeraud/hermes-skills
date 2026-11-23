#!/usr/bin/env python3
"""Prepare raw material for podcast show notes from a timestamped transcript.

Reads .srt, .vtt or a plain text file with lines like "[00:12:30] text" or
"00:12:30 text". Prints: duration, speaker names seen, links and spoken
domains, resource mentions (books, tools, articles), and "key moment"
candidates with real timestamps. It never invents anything: every item
printed comes from the transcript with its timestamp.

Usage:
  notes_prep.py FILE [--moments 8] [--format text|json]
  notes_prep.py --selftest
"""
import argparse, json, re, sys

TS = r'(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?'
RANGE = re.compile(TS + r'\s*-->\s*' + TS)
BRACKET = re.compile(r'^\[?' + TS + r'\]?\s*[-:]?\s*(.*)$')

def secs(h, m, s):
    return int(h or 0) * 3600 + int(m) * 60 + int(s)

def fmt(t):
    h, r = divmod(int(t), 3600)
    m, s = divmod(r, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

def parse(text):
    """Return list of (start_seconds, text)."""
    cues, lines = [], text.replace('\r', '').split('\n')
    i = 0
    if any(RANGE.search(l) for l in lines):
        while i < len(lines):
            m = RANGE.search(lines[i])
            if m:
                g = m.groups()
                start = secs(g[0], g[1], g[2])
                i += 1
                buf = []
                while i < len(lines) and lines[i].strip():
                    buf.append(re.sub(r'<[^>]+>', '', lines[i].strip()))
                    i += 1
                if buf:
                    cues.append((start, ' '.join(buf)))
            else:
                i += 1
        return cues
    for l in lines:
        m = BRACKET.match(l.strip())
        if m and m.group(5) is not None and (m.group(1) or m.group(2)):
            cues.append((secs(m.group(1), m.group(2), m.group(3)), m.group(5)))
        elif cues and l.strip():
            cues[-1] = (cues[-1][0], cues[-1][1] + ' ' + l.strip())
    return cues

URL = re.compile(r'https?://[^\s)>\]]+|www\.[^\s)>\]]+', re.I)
SPOKEN = re.compile(r'\b([a-z0-9][a-z0-9-]*(?:\s+(?:dot)\s+[a-z0-9-]+)+)\b', re.I)
RESOURCE = re.compile(
    r"\b(?:book|podcast|newsletter|article|tool|app|course|video|episode|"
    r"template|framework|study|report|website|site)\s+(?:called|named|titled)\s+"
    r"[\"“']?([A-Z0-9][\w'&:-]*(?:\s+[A-Za-z0-9][\w'&:-]*){0,5})", re.I)
RESOURCE2 = re.compile(
    r"\b(?:check out|go read|go watch|look up|I recommend|recommend)\s+"
    r"[\"“']?([A-Z0-9][\w'&:-]*(?:\s+[A-Z0-9][\w'&:-]*){0,4})")
SPEAKER = re.compile(r'^\s*(?:\[?\d[\d:.,]*\]?\s*)?([A-Z][A-Za-z]{1,19}(?: [A-Z][A-Za-z]{1,19})?):\s')
CUES = [r'\bthe (?:main|key|biggest|real) (?:thing|point|lesson|reason|mistake)\b',
        r'\bmy (?:advice|tip)\b', r'\bwhat (?:I|we) learned\b', r'\bthe mistake\b',
        r'\bif you (?:only|take one)\b', r'\bhere\'s (?:the|how|why)\b',
        r'\bthe (?:first|second|third|last) (?:step|thing|rule)\b', r'\bturning point\b',
        r'\bnever\b', r'\balways\b', r'\bbiggest\b', r'\bsurprising\b', r'\bwhy\b.*\?']
CUE_RE = [re.compile(c, re.I) for c in CUES]

def analyse(cues, moments=8):
    out = {'duration': fmt(cues[-1][0]) if cues else '0:00', 'cues': len(cues),
           'speakers': {}, 'links': [], 'spoken_domains': [], 'resources': [], 'moments': []}
    seen = set()
    for t, x in cues:
        m = SPEAKER.match(x)
        if m:
            out['speakers'][m.group(1)] = out['speakers'].get(m.group(1), 0) + 1
        for u in URL.findall(x):
            u = u.rstrip('.,;')
            if u not in seen:
                seen.add(u); out['links'].append({'at': fmt(t), 'url': u})
        for d in SPOKEN.findall(x):
            k = 'd:' + d.lower()
            if k not in seen:
                seen.add(k); out['spoken_domains'].append({'at': fmt(t), 'heard': d})
        for rx in (RESOURCE, RESOURCE2):
            for r in rx.findall(x):
                k = 'r:' + r.lower()
                if k not in seen:
                    seen.add(k); out['resources'].append({'at': fmt(t), 'name': r.strip(), 'context': x[:160]})
    scored = []
    for t, x in cues:
        n = len(x.split())
        if n < 6:
            continue
        s = sum(1 for c in CUE_RE if c.search(x)) * 2 + (1 if 12 <= n <= 45 else 0)
        if s >= 2:
            scored.append((s, t, x))
    scored.sort(key=lambda a: (-a[0], a[1]))
    picked = []
    for s, t, x in scored:
        if all(abs(t - p[1]) >= 120 for p in picked):
            picked.append((s, t, x))
        if len(picked) >= moments:
            break
    out['moments'] = [{'at': fmt(t), 'text': x} for s, t, x in sorted(picked, key=lambda a: a[1])]
    return out

def render(r):
    L = [f"Duration (last cue): {r['duration']} | cues: {r['cues']}"]
    if r['speakers']:
        L.append('Speaker labels seen: ' + ', '.join(f'{k} ({v})' for k, v in r['speakers'].items()))
    else:
        L.append('Speaker labels seen: none (ask who the host and guests are)')
    L.append('\nLinks said or written (verify before publishing):')
    L += [f"  [{i['at']}] {i['url']}" for i in r['links']] or ['  none']
    L.append('\nSpoken web addresses (heard, spelling to confirm):')
    L += [f"  [{i['at']}] {i['heard']}" for i in r['spoken_domains']] or ['  none']
    L.append('\nResource mentions (book, tool, article...):')
    L += [f"  [{i['at']}] {i['name']}  <- \"{i['context']}\"" for i in r['resources']] or ['  none']
    L.append('\nKey moment candidates:')
    L += [f"  [{i['at']}] {i['text']}" for i in r['moments']] or ['  none (read the transcript directly)']
    return '\n'.join(L)

SAMPLE = """1
00:00:02,000 --> 00:00:06,000
Alice: Welcome to the show, today we talk about newsletters.

2
00:03:10,000 --> 00:03:16,000
Bob: The biggest mistake I made was never writing down my own rules for sending.

3
00:07:00,000 --> 00:07:05,000
Alice: You should check out Simple Writing Tips, and the book called Tiny Habits Revisited.

4
00:09:30,000 --> 00:09:34,000
Bob: Everything is on example dot com slash start, or https://example.com/start.

5
00:15:45,000 --> 00:15:52,000
Bob: Here's why a small list that opens your email beats a big list that does not.
"""

def selftest():
    c = parse(SAMPLE)
    assert len(c) == 5 and c[1][0] == 190, c
    r = analyse(c)
    assert r['links'][0]['url'] == 'https://example.com/start', r['links']
    assert any('example dot com' in d['heard'] for d in r['spoken_domains']), r['spoken_domains']
    names = [x['name'] for x in r['resources']]
    assert any('Simple Writing Tips' in n for n in names) and any('Tiny Habits' in n for n in names), names
    assert set(r['speakers']) == {'Alice', 'Bob'}
    assert any(m['at'] == '3:10' for m in r['moments']), r['moments']
    plain = '[00:00:05] Alice: Hello there everybody\n[00:01:00] Bob: The key point is to publish weekly.'
    p = parse(plain)
    assert [x[0] for x in p] == [5, 60], p
    print('selftest OK')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file', nargs='?')
    ap.add_argument('--moments', type=int, default=8)
    ap.add_argument('--format', choices=['text', 'json'], default='text')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error('FILE required')
    cues = parse(open(a.file, encoding='utf-8', errors='replace').read())
    if not cues:
        sys.exit('No timestamps found. Export an SRT/VTT or lines like "[00:12:30] text".')
    r = analyse(cues, a.moments)
    print(json.dumps(r, indent=2, ensure_ascii=False) if a.format == 'json' else render(r))

if __name__ == '__main__':
    main()
