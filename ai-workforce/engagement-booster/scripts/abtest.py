#!/usr/bin/env python3
"""Size and read an A/B test for an engagement change, so "it worked" is backed by numbers.

  abtest.py size --baseline 0.12 --mde 0.02 [--alpha 0.05] [--power 0.8] [--daily-traffic 800] [--variants 2]
  abtest.py read --control 1200,148 --variant 1185,181 [--alpha 0.05]

size: visitors needed per variant to detect an absolute lift of --mde on a conversion rate (two-sided z-test),
      and the number of days at --daily-traffic (all variants together).
read: conversions as visitors,conversions per arm; prints rates, absolute and relative lift, 95% confidence
      interval of the difference, p-value and a plain verdict. It refuses to call a winner on tiny samples.
Standard library only.
"""
import argparse, math
from statistics import NormalDist

N = NormalDist()


def size(p, mde, alpha, power):
    p2 = p + mde
    za, zb = N.inv_cdf(1 - alpha / 2), N.inv_cdf(power)
    pbar = (p + p2) / 2
    n = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p * (1 - p) + p2 * (1 - p2))) ** 2 / mde ** 2
    return math.ceil(n)


def read(c, v, alpha):
    (n1, x1), (n2, x2) = c, v
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se0 = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) or 1e-12
    z = (p2 - p1) / se0
    pval = 2 * (1 - N.cdf(abs(z)))
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    zc = N.inv_cdf(1 - alpha / 2)
    return {'control_rate': p1, 'variant_rate': p2, 'abs_lift': p2 - p1, 'rel_lift': (p2 - p1) / p1 if p1 else float('inf'),
            'ci_low': p2 - p1 - zc * se, 'ci_high': p2 - p1 + zc * se, 'p_value': pval}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('size'); s.add_argument('--baseline', type=float, required=True); s.add_argument('--mde', type=float, required=True)
    s.add_argument('--alpha', type=float, default=0.05); s.add_argument('--power', type=float, default=0.8)
    s.add_argument('--daily-traffic', type=float); s.add_argument('--variants', type=int, default=2)
    r = sub.add_parser('read'); r.add_argument('--control', required=True); r.add_argument('--variant', required=True)
    r.add_argument('--alpha', type=float, default=0.05)
    a = ap.parse_args()
    if a.cmd == 'size':
        n = size(a.baseline, a.mde, a.alpha, a.power)
        print(f'Baseline {a.baseline:.1%}, detect +{a.mde:.1%} absolute (to {a.baseline + a.mde:.1%}), alpha {a.alpha}, power {a.power:.0%}')
        print(f'Needed: {n:,} visitors per variant, {n * a.variants:,} in total.')
        if a.daily_traffic:
            d = math.ceil(n * a.variants / a.daily_traffic)
            print(f'At {a.daily_traffic:,.0f} visitors/day: {d} days. Run whole weeks: {math.ceil(d / 7) * 7} days.')
        print('Decide the metric, the duration and the stop rule now, before looking at results.')
        return
    c = tuple(int(x) for x in a.control.split(',')); v = tuple(int(x) for x in a.variant.split(','))
    res = read(c, v, a.alpha)
    print(f"Control {res['control_rate']:.2%} ({c[1]}/{c[0]}) vs variant {res['variant_rate']:.2%} ({v[1]}/{v[0]})")
    print(f"Lift {res['abs_lift'] * 100:+.2f} pts ({res['rel_lift']:+.1%}), 95% CI {res['ci_low'] * 100:+.2f} to {res['ci_high'] * 100:+.2f} pts, p = {res['p_value']:.4f}")
    small = min(c[1], v[1], c[0] - c[1], v[0] - v[1]) < 30
    if small:
        print('Verdict: too few conversions for a reliable read. Keep the test running.')
    elif res['p_value'] < a.alpha:
        print('Verdict: ' + ('the variant wins' if res['abs_lift'] > 0 else 'the variant loses') + f" at the {1 - a.alpha:.0%} level, if the sample size was fixed in advance.")
    else:
        print('Verdict: no detectable difference. The change is at best small; do not ship it as a win.')


if __name__ == '__main__':
    main()
