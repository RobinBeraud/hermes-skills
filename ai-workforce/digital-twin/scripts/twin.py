#!/usr/bin/env python3
"""Keep a lightweight digital twin of a physical or technical system up to date from its readings.

  twin.py update spec.json readings.csv [--state twin_state.json] [--now 2026-11-10T12:00:00]
  twin.py status [--state twin_state.json] [--json]

spec.json describes the asset and each signal:
  {"asset": "Cold room 2", "signals": {"temp_c": {"min": 0, "max": 4, "stale_after_min": 30, "alpha": 0.3},
                                       "door_open": {"max": 0, "stale_after_min": 60}}}
readings.csv columns: timestamp, signal, value (one reading per row, any order, several assets allowed with --asset-col).

For each signal the twin keeps: last value and time, exponentially smoothed value (EWMA), min/max seen, number of
readings, out-of-range count, drift (EWMA vs first-seen baseline) and a status: ok, warning (smoothed value close to a
limit, or drifting), alert (last value outside limits) or stale (no reading for too long). The asset status is the worst
of its signals. State is a JSON file you can version, diff and feed to other agents. Standard library only.
"""
import argparse, csv, datetime as dt, json, os, sys

RANK = {'ok': 0, 'warning': 1, 'stale': 2, 'alert': 3}


def ts(s):
    return dt.datetime.fromisoformat(s.strip().replace('Z', '+00:00')).replace(tzinfo=None)


def evaluate(sig, spec, now):
    lo, hi = spec.get('min'), spec.get('max')
    v, e = sig['last'], sig['ewma']
    reasons = []
    status = 'ok'
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        status, reasons = 'alert', [f'last value {v} outside [{lo}, {hi}]']
    else:
        span = (hi - lo) if (lo is not None and hi is not None and hi > lo) else None
        margin = spec.get('warn_margin', 0.1)
        if span and (e > hi - margin * span or e < lo + margin * span):
            status, reasons = 'warning', [f'smoothed value {round(e, 3)} close to a limit']
        drift = spec.get('max_drift')
        if drift is not None and abs(e - sig['baseline']) > drift:
            status = 'warning'
            reasons.append(f"drift {round(e - sig['baseline'], 3)} vs baseline {sig['baseline']}")
    age = (now - ts(sig['last_time'])).total_seconds() / 60
    if spec.get('stale_after_min') and age > spec['stale_after_min'] and RANK['stale'] > RANK[status]:
        status, reasons = 'stale', [f'no reading for {round(age)} min'] + reasons
    sig['status'], sig['reasons'], sig['age_min'] = status, reasons, round(age, 1)


def update(spec, rows, state, now):
    asset = state.setdefault('asset', spec.get('asset', 'asset'))
    sigs = state.setdefault('signals', {})
    unknown = set()
    for r in sorted(rows, key=lambda r: ts(r['timestamp'])):
        name = r['signal'].strip()
        sp = spec['signals'].get(name)
        if sp is None:
            unknown.add(name); continue
        v = float(r['value'])
        s = sigs.get(name)
        if s is None:
            s = sigs[name] = {'baseline': v, 'ewma': v, 'min_seen': v, 'max_seen': v, 'count': 0, 'out_of_range': 0}
        a = sp.get('alpha', 0.3)
        s['ewma'] = round(a * v + (1 - a) * s['ewma'], 4)
        s['min_seen'], s['max_seen'] = min(s['min_seen'], v), max(s['max_seen'], v)
        s['count'] += 1
        if (sp.get('min') is not None and v < sp['min']) or (sp.get('max') is not None and v > sp['max']):
            s['out_of_range'] += 1
        s['last'], s['last_time'] = v, ts(r['timestamp']).isoformat()
    for name, s in sigs.items():
        evaluate(s, spec['signals'][name], now)
    for name in spec['signals']:
        if name not in sigs:
            sigs[name] = {'status': 'stale', 'reasons': ['never reported'], 'count': 0}
    state['status'] = max((s['status'] for s in sigs.values()), key=RANK.get, default='ok')
    state['updated_at'] = now.isoformat(timespec='seconds')
    state['ignored_signals'] = sorted(unknown)
    return state


def report(state):
    lines = [f"{state['asset']}: {state['status'].upper()} (updated {state['updated_at']})"]
    for name, s in sorted(state['signals'].items(), key=lambda kv: -RANK[kv[1]['status']]):
        if s.get('count'):
            lines.append(f"- {name}: {s['status']} | last {s['last']} at {s['last_time']} | smoothed {s['ewma']} | "
                         f"range seen {s['min_seen']} to {s['max_seen']} | out of range {s['out_of_range']}/{s['count']}"
                         + (f" | {'; '.join(s['reasons'])}" if s['reasons'] else ''))
        else:
            lines.append(f"- {name}: stale | never reported")
    if state.get('ignored_signals'):
        lines.append('Ignored (not in spec): ' + ', '.join(state['ignored_signals']))
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    u = sub.add_parser('update'); u.add_argument('spec'); u.add_argument('readings')
    u.add_argument('--state', default='twin_state.json'); u.add_argument('--now')
    st = sub.add_parser('status'); st.add_argument('--state', default='twin_state.json'); st.add_argument('--json', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'status':
        state = json.load(open(a.state, encoding='utf-8'))
        print(json.dumps(state, indent=2) if a.json else report(state)); return
    spec = json.load(open(a.spec, encoding='utf-8'))
    state = json.load(open(a.state, encoding='utf-8')) if os.path.exists(a.state) else {}
    rows = list(csv.DictReader(open(a.readings, encoding='utf-8-sig', newline='')))
    now = ts(a.now) if a.now else dt.datetime.now()
    state = update(spec, rows, state, now)
    json.dump(state, open(a.state, 'w', encoding='utf-8'), indent=2)
    print(report(state))
    sys.exit({'ok': 0, 'warning': 0, 'stale': 1, 'alert': 2}[state['status']])


if __name__ == '__main__':
    main()
