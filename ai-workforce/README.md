# AI Workforce: 20 agent roles for Hermes

Give your Hermes agent a team. Each folder is one role, written as a skill: when to call it, how it works step by step, three documented use cases with the exact request to make, the output format and its guardrails. Thirteen roles ship a tested Python script (standard library only) for the parts that must be computed rather than guessed.

| Role | What it does | Script |
|---|---|---|
| 💡 [Idea Generator](idea-generator/SKILL.md) | Structured brainstorming: diverge with five lenses, then a scored shortlist with a test for each idea | |
| 📐 [Design Prototyper](design-prototyper/SKILL.md) | From concept to a clickable single-file HTML prototype and a five-user test script | |
| ✍️ [Content Creator](content-creator/SKILL.md) | Original drafts for one audience and one channel, in your voice, every claim sourced | |
| 📊 [Data Visualizer](data-visualizer/SKILL.md) | Accessible SVG charts whose title states the insight | `chart.py` |
| 🔁 [Content Transformer](content-transformer/SKILL.md) | Repurpose and localise content between formats and languages, with a fidelity check | |
| 🧐 [Product Critic](product-critic/SKILL.md) | Rubric-based, constructive review with the top three fixes and what to keep | |
| 🛡️ [Content Guardian](content-guardian/SKILL.md) | Screens personal data, secrets, prompt injection and policy terms before publishing | `guard.py` |
| 🤝 [Interactive Companion](interactive-companion/SKILL.md) | Coach, tutor or onboarding guide that remembers goals and knows when to hand over | |
| 🧭 [Journey Personalizer](journey-personalizer/SKILL.md) | Auditable rules that assign each user a journey, with overlap and empty-rule checks | `personalize.py` |
| 🔬 [Research Assistant](research-assistant/SKILL.md) | Graded evidence, citations and confidence levels turned into actions | |
| 🧪 [Data Synthesizer](data-synthesizer/SKILL.md) | Reproducible synthetic datasets, or a privacy-safe twin of a real CSV | `synth.py` |
| 🔮 [Data Forecaster](data-forecaster/SKILL.md) | Backtested forecasts with 80% ranges | `forecast.py` |
| ⚖️ [Decision Optimizer](decision-optimizer/SKILL.md) | Weighted criteria, hard constraints and a sensitivity test on the winner | `decide.py` |
| ⚙️ [Workflow Automaton](workflow-automaton/SKILL.md) | Retries what is transient, escalates what is not, with a ready-to-read note | `run_guarded.py` |
| 📈 [Trend Watcher](trend-watcher/SKILL.md) | Emerging and fading topics in tickets, reviews, posts or news titles | `trends.py` |
| 🚨 [Anomaly Detector](anomaly-detector/SKILL.md) | Spikes, drops, level shifts and silent data in any metric, cron-friendly | `anomalies.py` |
| 🎲 [Digital Simulation](digital-simulation/SKILL.md) | Monte Carlo what-ifs: P10, median, P90 and the odds of hitting a target | `simulate.py` |
| 🛰️ [Digital Twin](digital-twin/SKILL.md) | Live JSON state of a system from its readings, with drift and staleness | `twin.py` |
| 📉 [Engagement Assessor](engagement-assessor/SKILL.md) | Active users, stickiness, cohort retention and funnels from an event log | `engagement.py` |
| 🚀 [Engagement Booster](engagement-booster/SKILL.md) | Behaviour-based interventions proven by a sized A/B test, no dark patterns | `abtest.py` |

## Install

```bash
# one role
hermes skills install RobinBeraud/hermes-skills/ai-workforce/data-forecaster
# or copy the whole team
cp -r ai-workforce ~/.hermes/skills/
```

Then ask in plain words: *"Use the decision-optimizer to compare these three CRMs"*, *"Every Monday, run the trend-watcher on last month's tickets"*.

## Combine roles into workflows

- **Launch a new offer:** Idea Generator → Product Critic → Design Prototyper → Digital Simulation (break-even odds) → Content Creator → Content Guardian.
- **Weekly operations review:** Anomaly Detector + Digital Twin (what broke) → Data Forecaster (what is coming) → Data Visualizer (one chart per message) → Workflow Automaton (schedule and escalate).
- **Grow retention:** Engagement Assessor (where people drop) → Trend Watcher (what they complain about) → Journey Personalizer (who gets what) → Engagement Booster (prove it with a test).
- **Decide with evidence:** Research Assistant → Decision Optimizer → Product Critic on the recommendation.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

All scripts are covered by `tests/test_ai_workforce.py` and run in CI on every pull request.
