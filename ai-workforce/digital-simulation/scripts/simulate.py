#!/usr/bin/env python3
"""Monte Carlo simulation of a scenario model described in JSON: test "what if" before doing it for real.

  simulate.py model.json [--runs 10000] [--seed 1] [--set var=value ...] [--json]

model.json:
  {"inputs": {"visitors": {"dist": "triangular", "low": 8000, "mode": 10000, "high": 15000},
              "conversion": {"dist": "normal", "mean": 0.025, "sd": 0.005, "min": 0},
              "price": {"value": 49}},
   "outputs": {"revenue": "visitors * conversion * price"},
   "targets": {"revenue": {"above": 10000}}}

Distributions: value (fixed), uniform(low, high), triangular(low, mode, high), normal(mean, sd, min?, max?),
lognormal(mu, sigma), choice(values: {value: weight}), bernoulli(p). Output formulas may use + - * / ** % (),
min(), max(), abs(), round(), if_(cond, a, b) and comparisons; they are parsed safely (no eval).
--set fixes an input to a value, for one-factor what-if tests. Standard library only.
"""
import argparse, ast, json, math, operator, random, statistics, sys

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos,
       ast.Gt: operator.gt, ast.Lt: operator.lt, ast.GtE: operator.ge, ast.LtE: operator.le, ast.Eq: operator.eq}
FUNCS = {'min': min, 'max': max, 'abs': abs, 'round': round, 'sqrt': math.sqrt, 'log': math.log,
         'if_': lambda c, a, b: a if c else b}


def safe_eval(expr, env):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in env:
                raise NameError(f'unknown variable {n.id!r} in {expr!r}')
            return env[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in OPS:
            return OPS[type(n.ops[0])](ev(n.left), ev(n.comparators[0]))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCS and not n.keywords:
            return FUNCS[n.func.id](*[ev(x) for x in n.args])
        raise ValueError(f'not allowed in formula: {ast.dump(n)[:60]}')
    return ev(ast.parse(expr, mode='eval'))


def draw(spec, rng):
    d = spec.get('dist', 'value')
    if d == 'value':
        return spec['value']
    if d == 'uniform':
        return rng.uniform(spec['low'], spec['high'])
    if d == 'triangular':
        return rng.triangular(spec['low'], spec['high'], spec['mode'])
    if d == 'normal':
        v = rng.gauss(spec['mean'], spec['sd'])
        return min(spec.get('max', v), max(spec.get('min', v), v))
    if d == 'lognormal':
        return rng.lognormvariate(spec['mu'], spec['sigma'])
    if d == 'choice':
        return rng.choices(list(spec['values']), weights=list(spec['values'].values()))[0]
    if d == 'bernoulli':
        return 1 if rng.random() < spec['p'] else 0
    raise ValueError(f'unknown dist {d!r}')


def pct(xs, q):
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def simulate(model, runs, seed, fixed):
    rng = random.Random(seed)
    inputs = dict(model['inputs'])
    for k, v in fixed.items():
        if k not in inputs:
            sys.exit(f'--set: unknown input {k!r}')
        inputs[k] = {'value': v}
    res = {k: [] for k in model['outputs']}
    for _ in range(runs):
        env = {k: draw(s, rng) for k, s in inputs.items()}
        for k, f in model['outputs'].items():  # outputs can reuse earlier outputs
            env[k] = safe_eval(f, env)
            res[k].append(float(env[k]))
    summary = {}
    for k, xs in res.items():
        xs.sort()
        s = {'mean': statistics.mean(xs), 'p10': pct(xs, .1), 'p50': pct(xs, .5), 'p90': pct(xs, .9), 'min': xs[0], 'max': xs[-1]}
        t = model.get('targets', {}).get(k)
        if t:
            if 'above' in t:
                s['prob_above_%s' % t['above']] = sum(x > t['above'] for x in xs) / runs
            if 'below' in t:
                s['prob_below_%s' % t['below']] = sum(x < t['below'] for x in xs) / runs
        summary[k] = {a: round(b, 4) for a, b in s.items()}
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('model'); ap.add_argument('--runs', type=int, default=10000); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--set', action='append', default=[], metavar='VAR=VALUE'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    fixed = {}
    for s in a.set:
        k, v = s.split('=', 1)
        fixed[k.strip()] = float(v)
    model = json.load(open(a.model, encoding='utf-8'))
    out = simulate(model, a.runs, a.seed, fixed)
    if a.json:
        print(json.dumps({'runs': a.runs, 'fixed': fixed, 'outputs': out}, indent=2)); return
    print(f"{a.runs} runs" + (f", fixed: {fixed}" if fixed else '') + (f"\n{model['question']}" if model.get('question') else ''))
    print('\n| Output | P10 | Median | P90 | Mean | Target |\n|---|---|---|---|---|---|')
    for k, s in out.items():
        tgt = ', '.join(f"{p.replace('prob_', '').replace('_', ' ')}: {v:.0%}" for p, v in s.items() if p.startswith('prob_'))
        print(f"| {k} | {s['p10']:,.2f} | {s['p50']:,.2f} | {s['p90']:,.2f} | {s['mean']:,.2f} | {tgt or '-'} |")
    print('\nRead P10-P90 as "8 times out of 10 the result lands in this range", under the stated assumptions.')


if __name__ == '__main__':
    main()
