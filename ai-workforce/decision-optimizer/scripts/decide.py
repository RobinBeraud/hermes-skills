#!/usr/bin/env python3
"""Rank options against weighted criteria, apply hard constraints, and test how robust the winner is.

  decide.py decision.json [--json]

decision.json:
  {"criteria": [{"name": "cost", "weight": 3, "direction": "min"}, {"name": "quality", "weight": 5}],
   "constraints": [{"criterion": "cost", "max": 50000}],
   "options": [{"name": "Vendor A", "cost": 42000, "quality": 7}, ...]}

Scores are min-max normalised per criterion (0 = worst option, 1 = best), multiplied by normalised weights and
summed. Sensitivity: each weight is moved -50% / +50% and the script reports whether the winner changes, then the
smallest single-weight change that would make the runner-up win. Standard library only.
"""
import argparse, json, sys


def score(options, criteria):
    total_w = sum(c['weight'] for c in criteria) or 1
    rng = {}
    for c in criteria:
        vals = [o[c['name']] for o in options]
        rng[c['name']] = (min(vals), max(vals))
    out = []
    for o in options:
        s, parts = 0.0, {}
        for c in criteria:
            lo, hi = rng[c['name']]
            x = 0.5 if hi == lo else (o[c['name']] - lo) / (hi - lo)
            if c.get('direction', 'max') == 'min':
                x = 1 - x
            parts[c['name']] = round(x * c['weight'] / total_w, 4)
            s += parts[c['name']]
        out.append({'name': o['name'], 'score': round(s, 4), 'contributions': parts})
    return sorted(out, key=lambda r: -r['score'])


def feasible(options, constraints):
    keep, dropped = [], []
    for o in options:
        why = [f"{k['criterion']} {o[k['criterion']]} > max {k['max']}" for k in constraints if 'max' in k and o[k['criterion']] > k['max']]
        why += [f"{k['criterion']} {o[k['criterion']]} < min {k['min']}" for k in constraints if 'min' in k and o[k['criterion']] < k['min']]
        (dropped.append({'name': o['name'], 'reasons': why}) if why else keep.append(o))
    return keep, dropped


def sensitivity(options, criteria):
    base = score(options, criteria)
    winner = base[0]['name']
    swings = []
    for i, c in enumerate(criteria):
        for f in (0.5, 1.5):
            cc = [dict(x) for x in criteria]
            cc[i]['weight'] = c['weight'] * f
            w = score(options, cc)[0]['name']
            if w != winner:
                swings.append(f"{c['name']} weight x{f} -> {w} wins")
    flip = None
    if len(base) > 1:
        runner = base[1]['name']
        for step in range(1, 41):  # up to x5 in 10% steps, on one criterion at a time
            for i, c in enumerate(criteria):
                cc = [dict(x) for x in criteria]
                cc[i]['weight'] = c['weight'] * (1 + step / 10)
                if score(options, cc)[0]['name'] == runner:
                    flip = f"raising '{c['name']}' weight by {step * 10}% makes {runner} win"
                    break
            if flip:
                break
    return swings, flip


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('decision'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    d = json.load(open(a.decision, encoding='utf-8'))
    crit, opts = d['criteria'], d['options']
    for o in opts:
        for c in crit:
            if c['name'] not in o:
                sys.exit(f"option {o['name']!r} has no value for criterion {c['name']!r}")
    keep, dropped = feasible(opts, d.get('constraints', []))
    if not keep:
        print(json.dumps({'error': 'no option satisfies the constraints', 'dropped': dropped}, indent=2)); sys.exit(1)
    ranking = score(keep, crit)
    swings, flip = sensitivity(keep, crit) if len(keep) > 1 else ([], None)
    res = {'ranking': ranking, 'dropped': dropped, 'robust': not swings, 'swings': swings, 'closest_flip': flip,
           'margin': round(ranking[0]['score'] - ranking[1]['score'], 4) if len(ranking) > 1 else None}
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False)); return
    names = [c['name'] for c in crit]
    print('| Rank | Option | Score | ' + ' | '.join(names) + ' |')
    print('|---|---|---|' + '---|' * len(names))
    for i, r in enumerate(ranking, 1):
        print(f"| {i} | {r['name']} | {r['score']:.3f} | " + ' | '.join(f"{r['contributions'][n]:.3f}" for n in names) + ' |')
    for x in dropped:
        print(f"Excluded: {x['name']} ({'; '.join(x['reasons'])})")
    print(f"\nWinner: {ranking[0]['name']}" + (f", margin {res['margin']:.3f}" if res['margin'] is not None else ''))
    print('Robust to +/-50% on any single weight.' if not swings else 'Fragile: ' + '; '.join(swings))
    if flip:
        print('Closest flip: ' + flip)


if __name__ == '__main__':
    main()
