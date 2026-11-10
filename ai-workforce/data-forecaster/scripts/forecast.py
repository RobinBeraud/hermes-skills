#!/usr/bin/env python3
"""Forecast a time series from a CSV with honest backtesting and prediction intervals.

  forecast.py data.csv --date-col date --value-col sales [--period month] [--horizon 6] [--season 12] [--json]

Steps: aggregate by period (day, week, month), backtest five methods on the last `horizon` points
(naive, seasonal naive, seasonal naive with drift, linear trend, Holt smoothing), keep the one with the lowest
MAE, refit on all data and forecast with an 80% interval from backtest errors. Standard library only.
"""
import argparse, csv, datetime as dt, json, statistics, sys


def parse_date(s):
    s = s.strip()[:10]
    for f in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    raise ValueError(f'unreadable date: {s!r}')


def bucket(d, period):
    if period == 'week':
        return d - dt.timedelta(days=d.weekday())
    if period == 'month':
        return d.replace(day=1)
    return d


def step(d, period, k=1):
    if period == 'day':
        return d + dt.timedelta(days=k)
    if period == 'week':
        return d + dt.timedelta(weeks=k)
    m = d.month - 1 + k
    return d.replace(year=d.year + m // 12, month=m % 12 + 1, day=1)


def load(path, dcol, vcol, period):
    agg = {}
    for r in csv.DictReader(open(path, encoding='utf-8-sig', newline='')):
        if not r.get(dcol) or r.get(vcol) in (None, ''):
            continue
        b = bucket(parse_date(r[dcol]), period)
        agg[b] = agg.get(b, 0.0) + float(r[vcol].replace(',', '.'))
    if not agg:
        sys.exit('no data')
    keys = sorted(agg)
    out, d = [], keys[0]
    while d <= keys[-1]:  # fill empty periods with 0 so the series is regular
        out.append((d, agg.get(d, 0.0)))
        d = step(d, period)
    return out


def m_naive(y, h, s):
    return [y[-1]] * h


def m_seasonal(y, h, s):
    if len(y) < s:
        return m_naive(y, h, s)
    return [y[len(y) - s + (i % s)] for i in range(h)]


def m_seasonal_drift(y, h, s):
    if len(y) < 2 * s:
        return m_seasonal(y, h, s)
    drift = statistics.mean(y[len(y) - s + i] - y[len(y) - 2 * s + i] for i in range(s))  # average year-on-year change
    return [y[len(y) - s + (i % s)] + drift * (1 + i // s) for i in range(h)]


def m_linear(y, h, s):
    n = len(y)
    xm, ym = (n - 1) / 2, statistics.mean(y)
    sxx = sum((i - xm) ** 2 for i in range(n)) or 1
    b = sum((i - xm) * (v - ym) for i, v in enumerate(y)) / sxx
    a = ym - b * xm
    return [a + b * (n + i) for i in range(h)]


def m_holt(y, h, s):
    best = None
    for alpha in (0.2, 0.4, 0.6, 0.8):
        for beta in (0.05, 0.1, 0.2, 0.4):
            lvl, tr, err = y[0], (y[1] - y[0]) if len(y) > 1 else 0, 0.0
            for v in y[1:]:
                err += abs(v - (lvl + tr))
                nl = alpha * v + (1 - alpha) * (lvl + tr)
                tr = beta * (nl - lvl) + (1 - beta) * tr
                lvl = nl
            if best is None or err < best[0]:
                best = (err, lvl, tr)
    _, lvl, tr = best
    return [lvl + tr * (i + 1) for i in range(h)]


METHODS = {'naive': m_naive, 'seasonal_naive': m_seasonal, 'seasonal_drift': m_seasonal_drift,
           'linear_trend': m_linear, 'holt': m_holt}


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def run(series, horizon, season):
    y = [v for _, v in series]
    if len(y) < horizon + 3:
        sys.exit(f'need at least {horizon + 3} periods, got {len(y)}: lower --horizon or use a finer --period')
    train, test = y[:-horizon], y[-horizon:]
    scores = {}
    for name, f in METHODS.items():
        pred = f(train, horizon, season)
        errs = [t - p for t, p in zip(test, pred)]
        scores[name] = {'mae': statistics.mean(abs(e) for e in errs), 'errors': errs}
    best = min(scores, key=lambda k: scores[k]['mae'])
    fc = METHODS[best](y, horizon, season)
    errs = scores[best]['errors']
    spread = max(quantile([abs(e) for e in errs], 0.8), 1e-9)  # 80% of backtest errors were smaller than this
    lo, hi = -spread, spread
    mean_abs = statistics.mean(abs(v) for v in test) or 1
    return {
        'periods_used': len(y), 'method': best,
        'backtest_mae': {k: round(v['mae'], 2) for k, v in sorted(scores.items(), key=lambda kv: kv[1]['mae'])},
        'backtest_mape_pct': round(100 * scores[best]['mae'] / mean_abs, 1),
        'forecast': [{'period': None, 'value': round(v, 2), 'low80': round(v + lo, 2), 'high80': round(v + hi, 2)} for v in fc],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv'); ap.add_argument('--date-col', default='date'); ap.add_argument('--value-col', default='value')
    ap.add_argument('--period', choices=['day', 'week', 'month'], default='month')
    ap.add_argument('--horizon', type=int, default=6); ap.add_argument('--season', type=int)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    season = a.season or {'day': 7, 'week': 52, 'month': 12}[a.period]
    series = load(a.csv, a.date_col, a.value_col, a.period)
    res = run(series, a.horizon, season)
    d = series[-1][0]
    for i, f in enumerate(res['forecast'], 1):
        f['period'] = step(d, a.period, i).isoformat()
    res['history_tail'] = [{'period': p.isoformat(), 'value': round(v, 2)} for p, v in series[-a.horizon:]]
    if a.json:
        print(json.dumps(res, indent=2)); return
    print(f"Method kept: {res['method']} (backtest MAE {res['backtest_mae'][res['method']]}, ~{res['backtest_mape_pct']}% of actuals)")
    print('Backtest MAE by method: ' + ', '.join(f'{k} {v}' for k, v in res['backtest_mae'].items()))
    print(f"\n| {a.period} | forecast | 80% interval |\n|---|---|---|")
    for f in res['forecast']:
        print(f"| {f['period']} | {f['value']} | {f['low80']} to {f['high80']} |")
    print(f"\nBased on {res['periods_used']} periods. Intervals come from backtest errors: wider when history is short or noisy.")


if __name__ == '__main__':
    main()
