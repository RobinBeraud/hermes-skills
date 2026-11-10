---
name: digital-twin
description: Maintain a lightweight digital twin of a physical or technical system (cold room, machine, server, building, fleet) from its readings, with a dependency-free Python script that tracks every signal's last value, smoothed value, drift, staleness and health in a versionable JSON state. Use when an agent should know the live state of a system and explain it.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [digital-twin, iot, monitoring, sensors, predictive-maintenance, state, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [anomaly-detector, digital-simulation, workflow-automaton]
---

# Digital Twin

The Digital Twin agent keeps a dynamic virtual copy of a real system. Each time readings arrive, it updates a JSON state: per signal the last value and time, an exponentially smoothed value, the range seen, how often it went out of bounds, its drift from the first baseline, and a status (ok, warning, stale, alert). The asset's status is the worst of its signals. Because the state is a plain file, Hermes can read it, explain it, compare it with yesterday's version and act on it.

## When to use

- Sensors or exports report on equipment (temperature, power, vibration, pressure, fill level) and someone should be told in plain language when it degrades.
- You want a single source of truth on "how is this system right now?" that agents and humans share.
- You plan predictive maintenance and need history and drift per signal first.

## How the agent works

1. **Model the asset** in `spec.json`: each signal with its safe range (`min`, `max`), smoothing (`alpha`), how long silence is acceptable (`stale_after_min`), and optional `max_drift` from baseline.
2. **Feed readings** as `timestamp,signal,value` rows (from an IoT export, an API poll or a CSV drop). Unknown signals are listed, not silently ignored.
3. **Update the twin** with `twin.py update`. The state file keeps memory across runs.
4. **Explain:** for warnings and alerts, the agent writes the likely cause and the action ("temperature above 4 °C for 10 minutes after the door was open: check the door seal, move sensitive stock").
5. **Act or escalate:** exit code 2 on alert and 1 on stale lets a cron job notify only when needed; repeated alerts go through `workflow-automaton`.

## Usage

```bash
python3 scripts/twin.py update examples/cold_room.spec.json examples/readings.csv --state cold_room_state.json
python3 scripts/twin.py status --state cold_room_state.json
python3 scripts/twin.py status --state cold_room_state.json --json
```

Example output on the bundled cold-room readings (checked at 09:10):

```
Cold room 2 (kitchen): ALERT (updated 2026-11-10T09:10:00)
- temp_c: alert | last 4.4 at 2026-11-10T09:00:00 | smoothed 3.2535 | range seen 2.1 to 4.4 | out of range 1/5 | last value 4.4 outside [0, 4]
- humidity_pct: stale | last 86.0 at 2026-11-10T08:00:00 | smoothed 86.0 | range seen 86.0 to 86.0 | out of range 0/1 | no reading for 70 min
- door_open: ok | last 0.0 at 2026-11-10T08:45:00 | smoothed 0.25 | range seen 0.0 to 1.0 | out of range 1/3
- compressor_kw: ok | last 2.4 at 2026-11-10T09:00:00 | smoothed 1.8699 | range seen 1.1 to 2.4 | out of range 0/5
Ignored (not in spec): vibration_mm_s
```

Exit codes: `0` ok or warning, `1` stale, `2` alert.

## Documented use cases

### 1. Restaurant cold room (food safety)
- **Ask Hermes:** "digital-twin: every 10 minutes update the cold room twin from the sensor export and WhatsApp me on alert, with what to do."
- **What you get:** alerts like "Cold room 2 at 4.4 °C (limit 4) since 09:00, compressor at full power after the door opened at 08:30: check the seal", plus a daily summary for the HACCP log.

### 2. Server fleet health
- **Ask Hermes:** "Build a twin per server from the hourly metrics (disk %, load, backup age) and tell me which ones drift."
- **What you get:** one state file per server and a morning list of drifting signals ("disk on web-2 up 9 points since baseline").

### 3. Before a maintenance visit
- **Ask Hermes:** "Summarise the twin of pump 3 over the last month for the technician."
- **What you get:** out-of-range counts, drift per signal and the periods without data, in a one-page brief.

## Limits

- A state-and-rules twin, not a physics model: it tracks and explains, it does not simulate the machine. Pair it with `digital-simulation` for what-ifs.
- Safe ranges come from you or the manufacturer; wrong ranges give wrong statuses.
- Readings must be in chronological order per run or the script sorts them; very large files are better aggregated first.
- Safety-critical systems need certified monitoring. Use this as an extra layer, never as the only alarm.

## Testing

`tests/test_ai_workforce.py` runs the bundled cold-room scenario and checks the alert, the stale signal and the ignored one. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`anomaly-detector` (statistical anomalies on one signal), `digital-simulation` (test a change before doing it), `workflow-automaton` (escalate repeated alerts).
