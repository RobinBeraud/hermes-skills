#!/usr/bin/env python3
"""Detect anomalies in a metric time series: spikes, drops, level shifts and missing periods.

  anomalies.py metrics.csv --time-col ts --value-col value [--window 24] [--threshold 3.5] [--expect-every 60] [--json]

Robust method: each point is compared with the rolling median of the previous `window` points and scaled by the
median absolute deviation (MAD), so one outlier does not hide the next one. A level shift is reported when the
median of the last window differs from the previous window by more than `threshold` MADs.
--expect-every N (minutes) also reports gaps longer than 2 x N. Exit code 1 when anomalies are found (cron-friendly).
Standard library only.
"""
import argparse, csv, datetime as dt, json, statistics, sys


def parse_ts(s):
    s = s.strip().replace('Z', '+00:00')
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return dt.datetime.fromtimestamp(float(s), dt.timezone.utc)


def mad(xs, med):
    return statistics.median(abs(x - med) for x in xs) * 1.4826 or 1e-9


def detect(points, window, threshold):
    found = []
    vals = [v for _, v in points]
    for i in range(window, len(points)):
        hist = vals[i - window:i]
        med = statistics.median(hist)
        z = (vals[i] - med) / mad(hist, med)
        if abs(z) >= threshold:
            found.append({'time': points[i][0].isoformat(), 'kind': 'spike' if z > 0 else 'drop', 'value': vals[i],
                          'expected': round(med, 3), 'score': round(z, 1),
                          'severity': 'high' if abs(z) >= 2 * threshold else 'medium'})
    if len(vals) >= 2 * window:
        prev, last = vals[-2 * window:-window], vals[-window:]
        mp, ml = statistics.median(prev), statistics.median(last)
        shift = (ml - mp) / mad(prev, mp)
        if abs(shift) >= threshold:
            found.append({'time': points[-window][0].isoformat(), 'kind': 'level_shift_up' if shift > 0 else 'level_shift_down',
                          'value': round(ml, 3), 'expected': round(mp, 3), 'score': round(shift, 1), 'severity': 'high'})
    return found


def gaps(points, every_min):
    out = []
    for (a, _), (b, _) in zip(points, points[1:]):
        if (b - a).total_seconds() > 2 * every_min * 60:
            out.append({'time': a.isoformat(), 'kind': 'missing_data', 'value': None, 'expected': None,
                        'score': round((b - a).total_seconds() / 60, 1), 'severity': 'medium',
                        'note': f'no data for {round((b - a).total_seconds() / 60)} min'})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv'); ap.add_argument('--time-col', default='ts'); ap.add_argument('--value-col', default='value')
    ap.add_argument('--window', type=int, default=24); ap.add_argument('--threshold', type=float, default=3.5)
    ap.add_argument('--expect-every', type=float, help='expected minutes between points (gap detection)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    pts = []
    for r in csv.DictReader(open(a.csv, encoding='utf-8-sig', newline='')):
        if r.get(a.time_col) and r.get(a.value_col) not in (None, ''):
            pts.append((parse_ts(r[a.time_col]), float(r[a.value_col].replace(',', '.'))))
    pts.sort(key=lambda p: p[0])
    if len(pts) <= a.window:
        sys.exit(f'need more than {a.window} points (got {len(pts)}); lower --window')
    found = detect(pts, a.window, a.threshold) + (gaps(pts, a.expect_every) if a.expect_every else [])
    found.sort(key=lambda f: f['time'])
    if a.json:
        print(json.dumps({'points': len(pts), 'anomalies': found}, indent=2))
    else:
        print(f'{len(pts)} points, window {a.window}, threshold {a.threshold} MAD: {len(found)} anomaly(ies)')
        for f in found:
            exp = '' if f['expected'] is None else f" (expected ~{f['expected']})"
            print(f"- [{f['severity']}] {f['time']} {f['kind']}: {f.get('note') or f['value']}{exp}, score {f['score']}")
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
