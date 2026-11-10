---
name: workflow-automaton
description: Automate routine tasks safely: turn a manual procedure into a scheduled job with retries for transient failures, a lock against double runs, a JSON run log and a ready-to-read escalation note when a human is needed, using a dependency-free Python wrapper. Use when a recurring task should run on its own and only bother you when it truly fails.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [automation, cron, runbook, retries, escalation, ops, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [anomaly-detector, digital-twin, content-guardian]
---

# Workflow Automaton

The Workflow Automaton automates routine tasks while escalating complex issues. It writes the procedure down once, runs it on schedule, retries what is worth retrying (timeouts, rate limits, 503s), stops immediately on what retrying would make worse (expired credentials, bad input), and leaves a short escalation note that tells a human what failed, why, and what to do next.

## When to use

- A weekly or nightly chore (exports, syncs, reports, backups, invoice runs) is still done by hand.
- An existing cron job fails silently, or retries a 401 until the account gets locked.
- You want an agent to run tasks unattended, with a clear line between what it may fix and what it must hand over.

## How the agent works

1. **Write the runbook** with the user: trigger (schedule or event), steps, inputs, expected output, how to check success, who owns it, what the agent may do alone and what needs approval (sending to customers, paying, deleting).
2. **Make each step idempotent** (running twice does no harm) and observable (a clear exit code and a log line).
3. **Wrap the command** with `run_guarded.py`: name, retry budget, backoff, timeout, lock.
4. **Classify failures:** transient → retry with exponential backoff; auth or input → escalate at once; unknown → one retry, then escalate.
5. **Escalate well:** the note in `escalations.md` (or sent by Hermes to chat) has the failure type, the command, the suggested next step and the last lines of output. No wall of logs.
6. **Review monthly** the run log: success rate, retries, duration trend, tasks that should be fixed or retired.

## Usage

```bash
python3 scripts/run_guarded.py --name "nightly CRM export" --retries 3 --backoff 30 --timeout 900 \
  --lock /tmp/crm_export.lock --log runs.jsonl --escalate-file escalations.md -- python3 export_crm.py --since yesterday
```

Example: a flaky API is retried, an expired key is escalated without retry.

```
flaky-api: transient failure (exit 1), retry 1/2 in 0s
flaky-api: transient failure (exit 1), retry 2/2 in 0s
flaky-api: escalated (transient) -> esc.md
crm-sync: escalated (auth) -> esc.md
```

Escalation note written:

```
## 2026-11-10 15:26 · crm-sync needs a human
- **Failure type:** auth (exit code 1, 1 attempt(s))
- **Suggested next step:** Renew or check the credentials, then rerun. Retrying would only lock the account.
```

Exit codes: `0` success, `75` skipped because another run holds the lock, otherwise the task's own exit code.

## Documented use cases

### 1. Weekly reporting without the Monday scramble
- **Ask Hermes:** "workflow-automaton: every Monday 7:00, pull last week's sales, build the summary and post it to the team. Escalate to me if the export fails."
- **What you get:** a runbook, a cron entry calling the wrapper, and a message to you only on failure, with the reason and the fix.

### 2. Invoice reminders with a human gate
- **Ask Hermes:** "Each morning, list invoices 15 days overdue and draft reminders. I approve before anything is sent."
- **What you get:** an automated step that prepares drafts, and an approval step you answer in chat; sending is never automatic.

### 3. Hardening an existing cron job
- **Ask Hermes:** "This nightly sync fails twice a month. Wrap it so transient errors retry and real ones reach me."
- **What you get:** the same job behind `run_guarded.py`, a lock so overlapping runs stop, and a run log to see the failure pattern after a month.

## Guardrails and limits

- Automate the routine, not the judgement: payments, deletions, legal or customer-facing messages keep a human approval step.
- Failure classification uses exit codes and keywords; tune the patterns to your tools' error messages.
- The lock is a local file: for jobs running on several machines, use a shared lock.
- Never print secrets in task output; the tail is copied into the escalation note.

## Testing

`tests/test_ai_workforce.py` simulates a success, a transient failure with retries and an auth failure, and checks the log and the escalation note. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`anomaly-detector` and `digital-twin` (the checks it runs), `content-guardian` (screen what it publishes), Hermes cron jobs (the scheduler).
