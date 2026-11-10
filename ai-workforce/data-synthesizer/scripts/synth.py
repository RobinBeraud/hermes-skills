#!/usr/bin/env python3
"""Generate realistic synthetic tabular data from a JSON schema, or infer a privacy-safe schema from a real CSV.

  synth.py generate schema.json [--rows N] [--seed S] [--out data.csv]
  synth.py profile real.csv [--min-count 5] [--out schema.json]

Column types: id, int, float, choice, bool, date, name, email, text.
Options per column: null_rate, min, max, mean, sd, values ({value: weight}), p (bool),
start/end (date), depends_on {"column": ..., "slope": ...} (numeric), unique (choice/int).
Standard library only. Same seed, same data.
"""
import argparse, csv, datetime as dt, json, math, random, re, statistics, sys

FIRST = ['Alex', 'Camille', 'Sam', 'Noa', 'Lou', 'Maxime', 'Jordan', 'Charlie', 'Eden', 'Robin', 'Sasha', 'Morgan',
         'Lena', 'Hugo', 'Ines', 'Leo', 'Maya', 'Nora', 'Theo', 'Zoe', 'Adam', 'Emma', 'Liam', 'Sofia']
LAST = ['Martin', 'Bernard', 'Garcia', 'Silva', 'Rossi', 'Muller', 'Lopez', 'Petit', 'Moreau', 'Santos', 'Novak',
        'Leroy', 'Fontaine', 'Costa', 'Weber', 'Laurent', 'Roux', 'Ferreira', 'Dubois', 'Schmidt']
WORDS = ('fast simple clear late broken useful price support delivery quality team great slow refund login '
         'mobile invoice export report bug feature onboarding').split()


def gen_value(col, rng, row, i):
    t = col.get('type', 'text')
    if t == 'id':
        return col.get('prefix', '') + str(col.get('start', 1) + i)
    if t in ('int', 'float'):
        lo, hi = col.get('min'), col.get('max')
        if 'mean' in col:
            v = rng.gauss(col['mean'], col.get('sd', abs(col['mean']) * 0.2 or 1))
        else:
            v = rng.uniform(lo if lo is not None else 0, hi if hi is not None else 100)
        dep = col.get('depends_on')
        if dep and isinstance(row.get(dep['column']), (int, float)):
            v += dep.get('slope', 1) * row[dep['column']]
        if lo is not None:
            v = max(lo, v)
        if hi is not None:
            v = min(hi, v)
        return int(round(v)) if t == 'int' else round(v, col.get('decimals', 2))
    if t == 'choice':
        vals = col['values']
        if isinstance(vals, dict):
            return rng.choices(list(vals), weights=list(vals.values()))[0]
        return rng.choice(vals)
    if t == 'bool':
        return rng.random() < col.get('p', 0.5)
    if t == 'date':
        a = dt.date.fromisoformat(col.get('start', '2026-01-01'))
        b = dt.date.fromisoformat(col.get('end', '2026-12-31'))
        return (a + dt.timedelta(days=rng.randint(0, max(0, (b - a).days)))).isoformat()
    if t == 'name':
        return rng.choice(FIRST) + ' ' + rng.choice(LAST)
    if t == 'email':
        base = re.sub(r'[^a-z]', '.', str(row.get(col.get('from', ''), rng.choice(FIRST))).lower()).strip('.')
        return f'{base}.{i + 1}@example.com'
    n = rng.randint(col.get('min_words', 3), col.get('max_words', 9))
    return ' '.join(rng.choice(col.get('words', WORDS)) for _ in range(n)).capitalize()


def generate(schema, rows=None, seed=None):
    rng = random.Random(schema.get('seed', 42) if seed is None else seed)
    n = rows or schema.get('rows', 100)
    cols = schema['columns']
    out = []
    for i in range(n):
        row = {}
        for c in cols:
            row[c['name']] = None if rng.random() < c.get('null_rate', 0) else gen_value(c, rng, row, i)
        out.append(row)
    return [c['name'] for c in cols], out


def profile(path, min_count=5):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig', newline='')))
    if not rows:
        sys.exit('empty CSV')
    cols = []
    for name in rows[0]:
        vals = [r[name] for r in rows]
        present = [v for v in vals if v not in ('', None)]
        c = {'name': name, 'null_rate': round(1 - len(present) / len(vals), 3)}
        nums = []
        for v in present:
            try:
                nums.append(float(v.replace(',', '.')))
            except ValueError:
                break
        if present and len(nums) == len(present):
            c['type'] = 'int' if all(x.is_integer() for x in nums) else 'float'
            c.update(min=min(nums), max=max(nums), mean=round(statistics.mean(nums), 3),
                     sd=round(statistics.pstdev(nums), 3) or 1)
        elif present and all(re.match(r'^\d{4}-\d{2}-\d{2}', v) for v in present):
            ds = sorted(v[:10] for v in present)
            c.update(type='date', start=ds[0], end=ds[-1])
        elif present and all(v.lower() in ('true', 'false', '0', '1', 'yes', 'no') for v in present):
            c.update(type='bool', p=round(sum(v.lower() in ('true', '1', 'yes') for v in present) / len(present), 3))
        elif present and all('@' in v for v in present):
            c['type'] = 'email'
        else:
            freq = {}
            for v in present:
                freq[v] = freq.get(v, 0) + 1
            kept = {k: n for k, n in freq.items() if n >= min_count}
            if kept and len(kept) <= 50:
                other = len(present) - sum(kept.values())
                if other:
                    kept['OTHER'] = other
                c.update(type='choice', values=kept)
            else:
                c['type'] = 'text'  # free text or high-cardinality: never copied
        cols.append(c)
    return {'rows': len(rows), 'seed': 42, 'columns': cols,
            'note': f'Inferred from {path}. Rare categories (<{min_count}) grouped as OTHER; free text never copied.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('generate'); g.add_argument('schema'); g.add_argument('--rows', type=int); g.add_argument('--seed', type=int); g.add_argument('--out')
    p = sub.add_parser('profile'); p.add_argument('csv'); p.add_argument('--min-count', type=int, default=5); p.add_argument('--out')
    a = ap.parse_args()
    if a.cmd == 'profile':
        s = json.dumps(profile(a.csv, a.min_count), indent=2, ensure_ascii=False)
        (open(a.out, 'w', encoding='utf-8').write(s) if a.out else print(s))
        return
    header, rows = generate(json.load(open(a.schema, encoding='utf-8')), a.rows, a.seed)
    f = open(a.out, 'w', encoding='utf-8', newline='') if a.out else sys.stdout
    w = csv.DictWriter(f, fieldnames=header, lineterminator='\n')
    w.writeheader()
    for r in rows:
        w.writerow({k: ('' if v is None else v) for k, v in r.items()})
    if a.out:
        f.close()
        print(f'{len(rows)} rows written to {a.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
