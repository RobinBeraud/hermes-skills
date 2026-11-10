#!/usr/bin/env python3
"""Find emerging and fading topics in a stream of dated texts (tickets, reviews, posts, news titles, survey answers).

  trends.py items.csv --date-col date --text-col text [--recent-days 14] [--baseline-days 56] [--min-count 4] [--top 15] [--json]

Compares how often each word and two-word phrase appears per item in the recent window versus the baseline window
just before it. Lift = recent rate / baseline rate, with smoothing so rare terms do not explode. A term must appear in
at least --min-count recent items. Terms found in exactly the same items are merged into one line. English and French stop words are ignored. Also reads JSON Lines with --jsonl.
Standard library only.
"""
import argparse, csv, datetime as dt, json, re, sys

STOP = set('''a an and are as at be been but by can could do does for from had has have how i if in into is it its just
like me more my no not of on or our out so than that the their them then there these they this to too up us very was we
were what when which who why will with would you your about after all also any because before being both did each few
get got here him his her its me most much new now off once only other over own same she should some such through under
until while yes le la les un une des du de et en est pas pour que qui dans sur avec au aux ce ces cette il elle ils elles
je tu nous vous on ne plus par se sa son ses leur leurs mais ou donc car tres très bien fait faire été être avoir ai as
a y mon ma mes ton ta tes notre nos votre vos lui même comme tout tous toute toutes since every still ever again already never always really please thanks hello'''.split())


def tokens(text):
    words = [w for w in re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9'\-]+", text.lower()) if w not in STOP and not w.isdigit() and len(w) > 2]
    return set(words) | {a + ' ' + b for a, b in zip(words, words[1:])}


def parse_date(s):
    return dt.date.fromisoformat(s.strip()[:10])


def load(a):
    items = []
    if a.jsonl:
        for l in open(a.file, encoding='utf-8'):
            if l.strip():
                o = json.loads(l); items.append((parse_date(o[a.date_col]), o[a.text_col]))
    else:
        for r in csv.DictReader(open(a.file, encoding='utf-8-sig', newline='')):
            if r.get(a.date_col) and r.get(a.text_col):
                items.append((parse_date(r[a.date_col]), r[a.text_col]))
    return items


def analyse(items, recent_days, baseline_days, min_count, end=None):
    end = end or max(d for d, _ in items)
    r0 = end - dt.timedelta(days=recent_days - 1)
    b0 = r0 - dt.timedelta(days=baseline_days)
    recent = [t for d, t in items if r0 <= d <= end]
    base = [t for d, t in items if b0 <= d < r0]
    if not recent or not base:
        sys.exit(f'not enough data: {len(recent)} recent and {len(base)} baseline items; widen the windows')
    occ = {}  # term -> set of item ids (recent items are 'r<i>', baseline items 'b<i>')
    for prefix, texts in (('r', recent), ('b', base)):
        for i, t in enumerate(texts):
            for term in tokens(t):
                occ.setdefault(term, set()).add(prefix + str(i))
    nr, nb = len(recent), len(base)
    # terms that occur in exactly the same items are one signal (parts of a recurring sentence): keep the longest
    by_items = {}
    for term, ids in occ.items():
        by_items.setdefault(frozenset(ids), []).append(term)
    rows = []
    for ids, terms in by_items.items():
        terms.sort(key=lambda s: (-len(s.split()), -len(s), s))
        r = sum(1 for x in ids if x[0] == 'r')
        b = len(ids) - r
        rr, br = (r + 0.5) / (nr + 1), (b + 0.5) / (nb + 1)
        rows.append({'term': terms[0], 'also': terms[1:4], 'recent': r, 'baseline': b,
                     'recent_share_pct': round(100 * r / nr, 1), 'baseline_share_pct': round(100 * b / nb, 1),
                     'lift': round(rr / br, 2)})
    emerging = sorted([x for x in rows if x['recent'] >= min_count and x['lift'] >= 1.5], key=lambda x: (-x['lift'], -x['recent']))
    fading = sorted([x for x in rows if x['baseline'] >= min_count * baseline_days / recent_days / 2 and x['lift'] <= 0.5], key=lambda x: (x['lift'], -x['baseline']))
    return {'recent_window': [r0.isoformat(), end.isoformat()], 'baseline_window': [b0.isoformat(), (r0 - dt.timedelta(days=1)).isoformat()],
            'recent_items': nr, 'baseline_items': nb, 'emerging': emerging, 'fading': fading}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file'); ap.add_argument('--date-col', default='date'); ap.add_argument('--text-col', default='text')
    ap.add_argument('--jsonl', action='store_true'); ap.add_argument('--recent-days', type=int, default=14)
    ap.add_argument('--baseline-days', type=int, default=56); ap.add_argument('--min-count', type=int, default=4)
    ap.add_argument('--top', type=int, default=15); ap.add_argument('--end', help='last day of the recent window (default: latest item)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    res = analyse(load(a), a.recent_days, a.baseline_days, a.min_count, parse_date(a.end) if a.end else None)
    res['emerging'], res['fading'] = res['emerging'][:a.top], res['fading'][:a.top]
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False)); return
    print(f"Recent {res['recent_window'][0]} to {res['recent_window'][1]} ({res['recent_items']} items) vs baseline "
          f"{res['baseline_window'][0]} to {res['baseline_window'][1]} ({res['baseline_items']} items)\n")
    for title, key in (('Emerging', 'emerging'), ('Fading', 'fading')):
        print(f'{title}:')
        if not res[key]:
            print('  (none above thresholds)')
        for x in res[key]:
            print(f"  {x['term']:<28} {x['baseline_share_pct']:>5}% -> {x['recent_share_pct']:>5}% of items  (x{x['lift']}, {x['recent']} recent)" + (f"  + {', '.join(x['also'][:3])}" if x['also'] else ''))
        print()


if __name__ == '__main__':
    main()
