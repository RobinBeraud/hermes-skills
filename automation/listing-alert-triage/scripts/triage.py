#!/usr/bin/env python3
"""listing-alert-triage: extract price / surface / city from property alert
e-mails (plain text or .eml), compute price per m2, compare to a reference
and rank listings. Standard library only."""
import argparse, csv, email, html, io, json, re, sys
from email import policy
from pathlib import Path

PRICE_RE = re.compile(r'(?<![\d.,])(\d{1,3}(?:[ \u00a0\u202f.]\d{3})+|\d{4,8})\s*(?:€|eur\b|euros?\b)', re.I)
AREA_RE = re.compile(r'(?<![\d.,])(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:m²|m2|m\u00b2|metres? carres?|mètres? carrés?)', re.I)
CITY_POSTAL_RE = re.compile(r'\b(\d{5})\s+([A-ZÀ-ÖØ-Þ][\wÀ-ÿ\'\- ]{1,40}?)(?=\s*[\n,;.()|]|\s{2,}|$)')
CITY_BEFORE_POSTAL_RE = re.compile(r'(?m)^[ \t]*([A-ZÀ-ÖØ-Þ][\wÀ-ÿ\'\-]+(?:[ \-][A-ZÀ-ÖØ-Þ][\wÀ-ÿ\'\-]+){0,3})[ \t]*[,(\-]?[ \t]*\(?(\d{5})\)?[ \t]*$')
CITY_PREP_RE = re.compile(r'\b(?:à|a|in)\s+([A-ZÀ-ÖØ-Þ][\wÀ-ÿ\'\-]+(?:[ \-][A-ZÀ-ÖØ-Þ][\wÀ-ÿ\'\-]+){0,3})')
URL_RE = re.compile(r'https?://[^\s<>"\')]+')

def to_int(s):
    return int(re.sub(r'[ \u00a0\u202f.]', '', s))

def read_text(path):
    p = Path(path)
    raw = p.read_bytes()
    if p.suffix.lower() == '.eml':
        msg = email.message_from_bytes(raw, policy=policy.default)
        body = msg.get_body(preferencelist=('plain', 'html'))
        text = body.get_content() if body else ''
        if body is not None and body.get_content_type() == 'text/html':
            text = html_to_text(text)
        return text
    text = raw.decode('utf-8', errors='replace')
    if '<html' in text.lower() or '<table' in text.lower():
        text = html_to_text(text)
    return text

def html_to_text(s):
    s = re.sub(r'(?is)<(script|style).*?</\1>', ' ', s)
    s = re.sub(r'(?is)<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r' \2 \1 ', s)
    s = re.sub(r'(?i)<br\s*/?>|</(p|div|tr|li|h\d|table)>', '\n', s)
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    s = html.unescape(s)
    return re.sub(r'[ \t]+', ' ', s)

def split_blocks(text):
    """A listing block = chunk separated by blank lines or separator lines.
    Chunks with no price are merged into the next chunk (title lines)."""
    chunks = [c.strip() for c in re.split(r'\n\s*\n|\n[-=_*]{3,}\n', text) if c.strip()]
    blocks, pending = [], ''
    for c in chunks:
        has_price = bool(PRICE_RE.search(c))
        if has_price and AREA_RE.search(c):
            blocks.append((pending + '\n' + c).strip() if pending else c)
            pending = ''
        elif has_price or AREA_RE.search(c):
            # partial info: keep accumulating with neighbours
            pending = (pending + '\n' + c).strip()
            if PRICE_RE.search(pending) and AREA_RE.search(pending):
                blocks.append(pending)
                pending = ''
        else:
            pending = c if len(c) < 200 else ''
    return blocks

def parse_block(b):
    pm = PRICE_RE.search(b)
    am = AREA_RE.search(b)
    if not (pm and am):
        return None
    price = to_int(pm.group(1))
    area = float(am.group(1).replace(',', '.'))
    if area <= 0 or price <= 0:
        return None
    city = postal = None
    m = CITY_POSTAL_RE.search(b)
    m2 = CITY_BEFORE_POSTAL_RE.search(b)
    if m2:
        city, postal = m2.group(1).strip(), m2.group(2)
    elif m:
        postal, city = m.group(1), m.group(2).strip()
    else:
        m = CITY_PREP_RE.search(b)
        if m:
            city = m.group(1).strip()
    url = URL_RE.search(b)
    title = next((l.strip() for l in b.splitlines()
                  if l.strip() and not re.fullmatch(r'[-=_*\s]+', l)), '')[:90]
    return {'title': title, 'price': price, 'area_m2': area,
            'price_per_m2': round(price / area), 'city': city,
            'postal': postal, 'url': url.group(0) if url else None}

def norm(s):
    s = (s or '').lower()
    for a, b in zip('àâäéèêëîïôöùûüç', 'aaaeeeeiioouuuc'):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def load_refs(args):
    refs = {}
    if args.ref_file:
        data = json.loads(Path(args.ref_file).read_text())
        refs.update({norm(k): float(v) for k, v in data.items()})
    for item in args.ref or []:
        k, _, v = item.rpartition('=')
        refs[norm(k)] = float(v)
    return refs

def classify(l, refs, a):
    ref = refs.get(norm(l['city'])) if l['city'] else None
    if ref is None:
        ref = refs.get('default')
    l['ref_per_m2'] = ref
    reasons = []
    if ref:
        l['ratio'] = round(l['price_per_m2'] / ref, 2)
    else:
        l['ratio'] = None
    if a.max_price and l['price'] > a.max_price:
        reasons.append('over max price')
    if a.min_area and l['area_m2'] < a.min_area:
        reasons.append('below min surface')
    if a.max_area and l['area_m2'] > a.max_area:
        reasons.append('above max surface')
    if reasons:
        l['verdict'] = 'excluded'
    elif l['ratio'] is None:
        l['verdict'] = 'no-reference'
    elif l['ratio'] <= a.gem_ratio:
        l['verdict'] = 'GEM'
        reasons.append(f"{round((1 - l['ratio']) * 100)}% below reference")
    elif l['ratio'] <= a.watch_ratio:
        l['verdict'] = 'watch'
        reasons.append('slightly below/near reference')
    else:
        l['verdict'] = 'pass'
        reasons.append('at or above reference')
    if l['ratio'] is not None and l['ratio'] < a.suspect_ratio:
        l['verdict'] += '?'
        reasons.append('suspiciously cheap: check for error/scam/major defect')
    l['reasons'] = '; '.join(reasons)
    return l

ORDER = {'GEM': 0, 'GEM?': 0, 'watch': 1, 'watch?': 1, 'no-reference': 2, 'pass': 3, 'excluded': 4}

def run(texts, args):
    refs = load_refs(args)
    seen, out = set(), []
    for t in texts:
        for b in split_blocks(t):
            l = parse_block(b)
            if not l:
                continue
            key = (l['price'], l['area_m2'], norm(l['city']))
            if key in seen:
                continue
            seen.add(key)
            out.append(classify(l, refs, args))
    out.sort(key=lambda x: (ORDER.get(x['verdict'], 5), x['ratio'] if x['ratio'] is not None else 9))
    return out

def render(rows, fmt):
    if fmt == 'json':
        return json.dumps(rows, ensure_ascii=False, indent=2)
    if fmt == 'csv':
        f = io.StringIO()
        w = csv.DictWriter(f, fieldnames=['verdict', 'city', 'price', 'area_m2', 'price_per_m2', 'ref_per_m2', 'ratio', 'reasons', 'url', 'title', 'postal'])
        w.writeheader()
        w.writerows(rows)
        return f.getvalue()
    lines = []
    for r in rows:
        ratio = f"{r['ratio']:.2f}x" if r['ratio'] else 'n/a'
        lines.append(f"[{r['verdict']:<12}] {r['city'] or '?':<14} {r['price']:>9,} EUR  {r['area_m2']:>6g} m2  {r['price_per_m2']:>6,} EUR/m2  ref {r['ref_per_m2'] or 'n/a'}  ratio {ratio}".replace(',', ' '))
        if r['reasons']:
            lines.append(f"    -> {r['reasons']}")
        if r['url']:
            lines.append(f"    {r['url']}")
    return '\n'.join(lines) if lines else 'No listing with both a price and a surface was found.'

SAMPLE = """New listings for you

Bright 3-room flat
Lyon 69003
Price: 289 000 €
Surface: 72 m²
https://example.com/ad/1001

----------
Studio near the park
42 000 € - 18 m2 à Nowhereville
https://example.com/ad/1002

----------
House with garden, 95m2
Asking 215.000 EUR
33000 Bordeaux
https://example.com/ad/1003

----------
Renovated 2-room, 41,5 m2
Price 119 000 €
75011 Paris
https://example.com/ad/1004

Same flat again:
Lyon 69003
Price: 289 000 €
Surface: 72 m²
"""

def selftest():
    ns = argparse.Namespace(ref=['Lyon=5000', 'Bordeaux=4000', 'Paris=10500', 'default=3000'], ref_file=None,
                            max_price=None, min_area=20, max_area=None, gem_ratio=0.85, watch_ratio=0.97, suspect_ratio=0.5)
    rows = run([SAMPLE], ns)
    by = {r['url']: r for r in rows if r['url']}
    assert len(rows) == 4, rows            # duplicate removed
    assert by['https://example.com/ad/1001']['price_per_m2'] == 4014
    assert by['https://example.com/ad/1001']['verdict'] == 'GEM'      # 0.80x
    assert by['https://example.com/ad/1003']['price_per_m2'] == 2263
    assert by['https://example.com/ad/1003']['verdict'] == 'GEM'      # 0.57x, not below suspect ratio
    assert by['https://example.com/ad/1004']['verdict'] == 'GEM?'     # 0.27x: flagged suspicious
    assert by['https://example.com/ad/1002']['verdict'] == 'excluded' # 18 m2 < min 20
    assert by['https://example.com/ad/1001']['city'] == 'Lyon'
    return rows

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('files', nargs='*', help='.txt/.html/.eml files (use - for stdin)')
    ap.add_argument('--ref', action='append', metavar='CITY=EUR_PER_M2', help='reference price/m2; repeatable; CITY=default as fallback')
    ap.add_argument('--ref-file', help='JSON file {"City": price_per_m2}')
    ap.add_argument('--gem-ratio', type=float, default=0.85, help='price/m2 <= ratio*ref => GEM (default 0.85)')
    ap.add_argument('--watch-ratio', type=float, default=0.97, help='<= this => watch (default 0.97)')
    ap.add_argument('--suspect-ratio', type=float, default=0.5, help='below this, flag as suspicious (default 0.5)')
    ap.add_argument('--max-price', type=int)
    ap.add_argument('--min-area', type=float)
    ap.add_argument('--max-area', type=float)
    ap.add_argument('--format', choices=['text', 'json', 'csv'], default='text')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        rows = selftest()
        print(render(rows, 'text'))
        print('\nSELFTEST OK')
        return 0
    texts = []
    for f in a.files or ['-']:
        texts.append(sys.stdin.read() if f == '-' else read_text(f))
    print(render(run(texts, a), a.format))
    return 0

if __name__ == '__main__':
    sys.exit(main())
