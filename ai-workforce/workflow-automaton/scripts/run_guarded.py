#!/usr/bin/env python3
"""Run a routine task unattended: retry what is transient, stop on what is not, and escalate with a ready-to-read note.

  run_guarded.py --name "nightly export" [--retries 3] [--backoff 30] [--timeout 600] [--lock /tmp/export.lock]
                 [--log runs.jsonl] [--escalate-file escalations.md] -- COMMAND [ARGS...]

Classification of a failure, from exit code and the last lines of output:
  transient  (timeouts, 429, 502/503/504, "connection reset", "temporarily unavailable")  -> retried with backoff
  auth       (401/403, "permission denied", "invalid token", "expired")                    -> escalated, no retry
  input      ("no such file", "invalid", "parse error", exit code 2)                        -> escalated, no retry
  unknown    (anything else)                                                                -> one retry, then escalated
A lock file prevents two runs at once (a stale lock older than 6 hours is replaced). Each attempt is appended to
--log as one JSON line, and every escalation is appended to --escalate-file as a short Markdown note with the reason,
the suggested next step and the tail of the output. Exit code: 0 success, 75 skipped (locked), else the task's code.
Standard library only.
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, time

PATTERNS = [
    ('auth', re.compile(r'\b(401|403)\b|unauthori[sz]ed|forbidden|permission denied|invalid (api )?(key|token)|token expired|expired credentials', re.I)),
    ('transient', re.compile(r'timed? ?out|\b(429|502|503|504)\b|too many requests|connection (reset|refused|aborted)|temporar(il)?y unavailable|try again later|name resolution', re.I)),
    ('input', re.compile(r'no such file|not found: .*\.(csv|json|xml)|invalid (input|argument|format)|parse error|malformed|schema', re.I)),
]
NEXT = {'auth': 'Renew or check the credentials, then rerun. Retrying would only lock the account.',
        'input': 'Fix the input (file, path or format) named in the output, then rerun.',
        'transient': 'The remote service kept failing. Check its status page; rerun later or raise the retry budget.',
        'unknown': 'Read the output tail below; reproduce the command by hand before changing anything.'}


def classify(code, out):
    if code == 124 or code is None:
        return 'transient'
    for kind, rx in PATTERNS:
        if rx.search(out):
            return kind
    return 'input' if code == 2 else 'unknown'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True); ap.add_argument('--retries', type=int, default=3)
    ap.add_argument('--backoff', type=float, default=30); ap.add_argument('--timeout', type=float, default=600)
    ap.add_argument('--lock'); ap.add_argument('--log', default='runs.jsonl'); ap.add_argument('--escalate-file', default='escalations.md')
    ap.add_argument('cmd', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ['--'] else a.cmd
    if not cmd:
        sys.exit('give the command after --')
    if a.lock:
        if os.path.exists(a.lock) and time.time() - os.path.getmtime(a.lock) < 6 * 3600:
            print(f'{a.name}: already running (lock {a.lock}), skipped'); sys.exit(75)
        open(a.lock, 'w').write(str(os.getpid()))
    attempt, code, kind, tail = 0, 1, 'unknown', ''
    try:
        while True:
            attempt += 1
            t0 = time.time()
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout)
                code, out = p.returncode, (p.stdout or '') + (p.stderr or '')
            except subprocess.TimeoutExpired as e:
                code, out = 124, f'timed out after {a.timeout}s\n' + str(e.output or '')
            except FileNotFoundError as e:
                code, out = 127, f'no such file: {e}'
            tail = '\n'.join(out.strip().splitlines()[-15:])
            kind = 'ok' if code == 0 else classify(code, out)
            with open(a.log, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'ts': dt.datetime.now().isoformat(timespec='seconds'), 'task': a.name, 'attempt': attempt,
                                    'exit': code, 'class': kind, 'seconds': round(time.time() - t0, 1)}) + '\n')
            if code == 0:
                print(f'{a.name}: ok (attempt {attempt})'); return
            budget = a.retries if kind == 'transient' else (1 if kind == 'unknown' else 0)
            if attempt > budget:
                break
            wait = a.backoff * 2 ** (attempt - 1)
            print(f'{a.name}: {kind} failure (exit {code}), retry {attempt}/{budget} in {wait:.0f}s', file=sys.stderr)
            time.sleep(wait)
        note = (f"\n## {dt.datetime.now():%Y-%m-%d %H:%M} · {a.name} needs a human\n\n"
                f"- **Failure type:** {kind} (exit code {code}, {attempt} attempt(s))\n- **Command:** `{' '.join(cmd)}`\n"
                f"- **Suggested next step:** {NEXT[kind]}\n\n```\n{tail}\n```\n")
        with open(a.escalate_file, 'a', encoding='utf-8') as f:
            f.write(note)
        print(f'{a.name}: escalated ({kind}) -> {a.escalate_file}', file=sys.stderr)
        sys.exit(code or 1)
    finally:
        if a.lock and os.path.exists(a.lock):
            os.remove(a.lock)


if __name__ == '__main__':
    main()
