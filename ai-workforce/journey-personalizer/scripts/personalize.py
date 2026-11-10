#!/usr/bin/env python3
"""Assign each user to a personalised journey with explicit, auditable rules, and check the rules before going live.

  personalize.py users.csv rules.json [--out assignments.csv] [--explain USER_ID]

rules.json (first matching journey wins, so order matters):
  {"id_col": "user_id",
   "journeys": [
     {"name": "activation_rescue", "when": [["projects", "==", 0], ["days_since_signup", ">=", 3]],
      "message": "Your first project in 5 minutes", "channel": "email"},
     {"name": "team_upsell", "when": [["plan", "==", "pro"], ["seats_used", ">=", 4]], "channel": "in_app"}],
   "default": {"name": "nurture", "channel": "newsletter"},
   "exclude": [["opt_out", "==", "yes"]]}

Operators: == != > >= < <= in (list) contains (substring). Values are compared as numbers when both sides are numbers.
The report shows how many users land in each journey, users matching several journeys (overlaps hidden by the order),
journeys nobody matches, and excluded users. --explain prints why one user got their journey. Standard library only.
"""
import argparse, csv, json, sys
from collections import Counter


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def test(user, cond):
    field, op, val = cond
    u = user.get(field, '')
    a, b = num(u), num(val) if not isinstance(val, list) else None
    if op == 'in':
        return str(u) in [str(x) for x in val]
    if op == 'contains':
        return str(val).lower() in str(u).lower()
    if a is not None and b is not None:
        x, y = a, b
    else:
        x, y = str(u), str(val)
        if op in ('>', '>=', '<', '<='):
            return False  # never compare text with < or >
    return {'==': x == y, '!=': x != y, '>': x > y, '>=': x >= y, '<': x < y, '<=': x <= y}[op]


def assign(users, rules):
    idc = rules.get('id_col', 'user_id')
    rows, overlaps, counts = [], Counter(), Counter()
    for u in users:
        if any(test(u, c) for c in rules.get('exclude', [])):
            rows.append({'id': u.get(idc), 'journey': 'EXCLUDED', 'channel': '', 'also_matched': ''}); counts['EXCLUDED'] += 1; continue
        matched = [j for j in rules['journeys'] if all(test(u, c) for c in j['when'])]
        j = matched[0] if matched else rules.get('default', {'name': 'none'})
        if len(matched) > 1:
            overlaps[tuple(m['name'] for m in matched)] += 1
        counts[j['name']] += 1
        rows.append({'id': u.get(idc), 'journey': j['name'], 'channel': j.get('channel', ''),
                     'also_matched': ';'.join(m['name'] for m in matched[1:])})
    return rows, counts, overlaps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('users'); ap.add_argument('rules'); ap.add_argument('--out'); ap.add_argument('--explain')
    a = ap.parse_args()
    users = list(csv.DictReader(open(a.users, encoding='utf-8-sig', newline='')))
    rules = json.load(open(a.rules, encoding='utf-8'))
    if a.explain:
        idc = rules.get('id_col', 'user_id')
        u = next((x for x in users if x.get(idc) == a.explain), None)
        if not u:
            sys.exit(f'user {a.explain} not found')
        for c in rules.get('exclude', []):
            print(f"exclude {c}: {'MATCH' if test(u, c) else 'no'} (value {u.get(c[0])!r})")
        for j in rules['journeys']:
            print(f"{j['name']}:")
            for c in j['when']:
                print(f"  {c[0]} {c[1]} {c[2]!r} -> {'yes' if test(u, c) else 'NO'} (value {u.get(c[0])!r})")
        print('Assigned: ' + assign([u], rules)[0][0]['journey'])
        return
    rows, counts, overlaps = assign(users, rules)
    n = len(users)
    print(f'{n} users')
    for name in [j['name'] for j in rules['journeys']] + [rules.get('default', {}).get('name', 'none'), 'EXCLUDED']:
        if name in counts or name in [j['name'] for j in rules['journeys']]:
            c = counts.get(name, 0)
            print(f"  {name:<24} {c:>6}  {100 * c / n:5.1f}%" + ('   <- nobody matches: check the rule' if c == 0 and name != 'EXCLUDED' else ''))
    for combo, c in overlaps.most_common():
        print(f"  overlap: {c} user(s) match {' + '.join(combo)} -> only '{combo[0]}' applies")
    if a.out:
        w = csv.DictWriter(open(a.out, 'w', encoding='utf-8', newline=''), fieldnames=['id', 'journey', 'channel', 'also_matched'])
        w.writeheader(); w.writerows(rows)
        print(f'Assignments written to {a.out}')


if __name__ == '__main__':
    main()
