#!/usr/bin/env python3
"""Measure engagement from an event log: active users, stickiness, weekly cohort retention, funnel and top events.

  engagement.py events.csv [--user-col user_id] [--time-col timestamp] [--event-col event]
                [--funnel signup,first_project,invite_sent] [--active-events a,b] [--weeks 8] [--json]

--active-events limits what counts as "active" (default: any event), so passive events like email_opened do not
inflate engagement. Cohorts are based on each user's first event week (Monday). Funnel steps must happen in order,
per user, at any time after the previous step. Standard library only.
"""
import argparse, csv, datetime as dt, json, statistics
from collections import Counter, defaultdict


def ts(s):
    s = s.strip().replace('Z', '+00:00')
    d = dt.datetime.fromisoformat(s if 'T' in s or ' ' in s else s + 'T00:00:00')
    return d.replace(tzinfo=None)


def monday(d):
    d = d.date() if isinstance(d, dt.datetime) else d
    return d - dt.timedelta(days=d.weekday())


def analyse(rows, funnel, active_events, weeks):
    ev = sorted(rows, key=lambda r: r[1])
    end = ev[-1][1].date()
    active = [r for r in ev if not active_events or r[2] in active_events]
    def users_between(days):
        start = end - dt.timedelta(days=days - 1)
        return {u for u, t, _ in active if start <= t.date() <= end}
    daily = defaultdict(set)
    for u, t, _ in active:
        if t.date() > end - dt.timedelta(days=28):
            daily[t.date()].add(u)
    dau = statistics.mean(len(daily.get(end - dt.timedelta(days=i), ())) for i in range(28))
    mau = len(users_between(28))
    first = {}
    for u, t, _ in ev:
        first.setdefault(u, monday(t))
    activity = defaultdict(set)
    for u, t, _ in active:
        activity[u].add(monday(t))
    cohorts = defaultdict(list)
    for u, w in first.items():
        cohorts[w].append(u)
    last_week = monday(end)
    table = []
    for w in sorted(cohorts)[-weeks:]:
        us = cohorts[w]
        row = {'cohort_week': w.isoformat(), 'users': len(us), 'retention_pct': []}
        k = 0
        while w + dt.timedelta(weeks=k) <= last_week and k < weeks:
            wk = w + dt.timedelta(weeks=k)
            row['retention_pct'].append(round(100 * sum(1 for u in us if wk in activity[u]) / len(us)))
            k += 1
        table.append(row)
    fun = []
    if funnel:
        per_user = defaultdict(list)
        for u, t, e in ev:
            per_user[u].append(e)
        counts = [0] * len(funnel)
        for u, es in per_user.items():
            i = 0
            for e in es:
                if i < len(funnel) and e == funnel[i]:
                    counts[i] += 1; i += 1
        for i, (step, c) in enumerate(zip(funnel, counts)):
            fun.append({'step': step, 'users': c, 'from_start_pct': round(100 * c / counts[0], 1) if counts[0] else 0,
                        'from_previous_pct': round(100 * c / counts[i - 1], 1) if i and counts[i - 1] else 100.0})
    return {'period_end': end.isoformat(), 'users_total': len(first), 'dau_avg_28d': round(dau, 1),
            'wau': len(users_between(7)), 'mau': mau, 'stickiness_dau_mau_pct': round(100 * dau / mau, 1) if mau else 0,
            'cohorts': table, 'funnel': fun, 'top_events': Counter(e for _, _, e in ev).most_common(8)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv'); ap.add_argument('--user-col', default='user_id'); ap.add_argument('--time-col', default='timestamp')
    ap.add_argument('--event-col', default='event'); ap.add_argument('--funnel', default='')
    ap.add_argument('--active-events', default=''); ap.add_argument('--weeks', type=int, default=8)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    rows = [(r[a.user_col], ts(r[a.time_col]), r[a.event_col]) for r in csv.DictReader(open(a.csv, encoding='utf-8-sig', newline=''))
            if r.get(a.user_col) and r.get(a.time_col)]
    res = analyse(rows, [s for s in a.funnel.split(',') if s], set(s for s in a.active_events.split(',') if s), a.weeks)
    if a.json:
        print(json.dumps(res, indent=2)); return
    print(f"Up to {res['period_end']}: {res['users_total']} users | DAU {res['dau_avg_28d']} | WAU {res['wau']} | MAU {res['mau']} | "
          f"stickiness DAU/MAU {res['stickiness_dau_mau_pct']}%")
    print('\nWeekly retention (% of cohort active in week N):')
    print('| Cohort | Users | ' + ' | '.join(f'W{i}' for i in range(a.weeks)) + ' |')
    print('|---|---|' + '---|' * a.weeks)
    for c in res['cohorts']:
        cells = [f'{v}%' for v in c['retention_pct']] + [''] * (a.weeks - len(c['retention_pct']))
        print(f"| {c['cohort_week']} | {c['users']} | " + ' | '.join(cells) + ' |')
    if res['funnel']:
        print('\nFunnel:')
        for f in res['funnel']:
            print(f"  {f['step']:<22} {f['users']:>6} users  {f['from_start_pct']:>5}% of start  {f['from_previous_pct']:>5}% of previous")
    print('\nTop events: ' + ', '.join(f'{e} ({n})' for e, n in res['top_events']))


if __name__ == '__main__':
    main()
