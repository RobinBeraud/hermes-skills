---
name: anomaly-detector
description: Detect spikes, drops, level shifts and missing data in any metric time series (latency, sales, sign-ups, sensor values) with a robust, dependency-free Python script and a cron-friendly exit code. Use when you want to be told when a number stops behaving normally, without hand-tuned thresholds.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [anomaly-detection, monitoring, alerting, time-series, observability, cron, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [digital-twin, workflow-automaton, data-forecaster, data-visualizer]
---

# Anomaly Detector

The Anomaly Detector watches a metric and flags what is irregular: a sudden spike, a drop, a new normal after a deploy, or a silent collector. It compares each point with the rolling median of the previous points, scaled by the median absolute deviation (MAD), so one outlier does not hide the next and normal daily waves do not raise alarms.

## When to use

- An API, a site or a job should be watched without writing fixed thresholds.
- A business metric (orders, sign-ups, refunds) should trigger a message when it breaks pattern.
- A data pipeline must not stay silent: missing periods are anomalies too.

## How the agent works

1. **Pick the metric and the grain** (one point per 5 minutes, hour, day). Export it as CSV `timestamp,value`.
2. **Choose the window**: one cycle of normal variation (24 hourly points for a daily cycle, 28 daily points for weekly patterns).
3. **Run the script.** Spikes and drops come with the expected value and a score in MADs; level shifts compare the last window with the one before; `--expect-every` reports gaps.
4. **Triage like an on-call engineer:** for each anomaly, the likely cause (deploy, campaign, outage, data bug), who to tell, and whether it needs action now. Group duplicates (a level shift often starts with a spike).
5. **Schedule it** in a Hermes cron job: the script exits 1 when anomalies are found, so the job only reports when something is wrong. Wrap it with `workflow-automaton` for retries and escalation.

## Usage

```bash
python3 scripts/anomalies.py examples/api_latency.csv --time-col ts --value-col response_ms --window 24 --expect-every 15
python3 scripts/anomalies.py orders_daily.csv --time-col day --value-col orders --window 28 --threshold 4 --json
```

Example output on the bundled latency file (15-minute points, one spike, a collector outage and a regression after a deploy):

```
93 points, window 24, threshold 3.5 MAD: 4 anomaly(ies)
- [high] 2026-11-01T10:00:00 spike: 520.0 (expected ~179.4), score 16.6
- [medium] 2026-11-01T14:45:00 missing_data: no data for 60 min, score 60.0
- [medium] 2026-11-01T18:00:00 spike: 275.7 (expected ~179.9), score 3.6
- [high] 2026-11-01T18:00:00 level_shift_up: 274.4 (expected ~179.9), score 3.5
```

Exit codes: `0` nothing found, `1` anomalies found.

## Documented use cases

### 1. API latency after deployments
- **Ask Hermes:** "Every 15 minutes, run anomaly-detector on the p95 latency export and message me only on high severity."
- **What you get:** a cron job that stays silent on normal days and sends "level shift up at 18:00, +53%, right after deploy 412" when a release slows the API.

### 2. Daily sales watch for a shop
- **Ask Hermes:** "Check yesterday's orders against the last 4 weeks and tell me if it is abnormal."
- **What you get:** "Drop: 12 orders vs ~41 expected (score -6.2). Checkout errors in the logs since 14:00?" with a link to the logs to check.

### 3. Silent data pipelines
- **Ask Hermes:** "Alert me if the weather station stops sending data for more than 30 minutes."
- **What you get:** `--expect-every 10` reports every gap above 20 minutes, with its duration.

## Limits

- One series at a time, univariate. Correlated metrics (errors and latency together) need two runs and a human or agent to connect them.
- Strong trends inside the window can create false alarms; use a shorter window or detrend first.
- The first `window` points are never scored. Start with clean history.

## Testing

`tests/test_ai_workforce.py` generates a series with a planted spike, gap and shift and checks all three are found. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`digital-twin` (per-signal health of a system), `workflow-automaton` (retries and escalation notes), `data-forecaster` (clean the history before forecasting), `data-visualizer` (show the anomaly on a chart).
