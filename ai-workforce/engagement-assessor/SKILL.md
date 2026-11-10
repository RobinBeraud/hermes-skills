---
name: engagement-assessor
description: Measure how people really engage with a product, course, community or newsletter from an event log, with a dependency-free Python script for active users, stickiness, weekly cohort retention, funnels and top events. Use when you need to know whether users come back and where they drop off, not just how many signed up.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [engagement, retention, cohorts, funnel, product-analytics, dau-mau, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [engagement-booster, journey-personalizer, data-visualizer, trend-watcher]
---

# Engagement Assessor

The Engagement Assessor analyses human responses and engagement. From any event log (user, time, event) it computes active users per day, week and month, stickiness (DAU/MAU), weekly cohort retention, an ordered funnel and the most frequent events. You choose which events count as "active", so opening an e-mail or a page view does not pass for real use.

## When to use

- After a launch: do new users come back in week 1, week 4?
- An online course or community wants to know where learners drop out.
- Before investing in growth: fix retention first if cohorts fall to zero.
- To measure the effect of a change made by `engagement-booster`.

## How the agent works

1. **Define "active"** with the user: the events that prove value (created a project, completed a lesson, replied), not passive ones.
2. **Export events** as CSV `user_id,timestamp,event` from the product, LMS, CRM or newsletter tool. Pseudonymise user ids if needed.
3. **Run the script** with the active events and the key funnel (e.g. signup, first_project, invite_sent).
4. **Read the numbers like a product analyst:** biggest drop in the funnel, week-1 retention by cohort, whether recent cohorts do better than old ones, stickiness. Compare with your own history, not with internet benchmarks.
5. **Recommend** one or two hypotheses to test and hand them to `engagement-booster`. Chart retention or the funnel with `data-visualizer`.

## Usage

```bash
python3 scripts/engagement.py examples/events.csv --funnel signup,first_project,invite_sent \
  --active-events signup,first_project,invite_sent,edit_project,comment,export --weeks 6
python3 scripts/engagement.py lms_events.csv --user-col learner --time-col ts --event-col action --json
```

Example output on the bundled events:

```
Up to 2026-11-08: 240 users | DAU 6.8 | WAU 13 | MAU 99 | stickiness DAU/MAU 6.9%

| Cohort | Users | W0 | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|---|---|
| 2026-09-21 | 25 | 100% | 32% | 8% | 8% | 4% | 0% |
| 2026-10-19 | 23 | 100% | 35% | 4% |  |  |  |

Funnel:
  signup                    240 users  100.0% of start  100.0% of previous
  first_project             171 users   71.2% of start   71.2% of previous
  invite_sent                81 users   33.8% of start   47.4% of previous
```

## Documented use cases

### 1. SaaS onboarding check
- **Ask Hermes:** "engagement-assessor on last 2 months of events. Where do new users drop, and do they come back in week 1?"
- **What you get:** "71% create a first project, but only 47% of them invite someone; week-1 retention is 14 to 35% and collapses by week 2. Hypothesis: invite step comes too late." Plus two charts.

### 2. Online course completion
- **Ask Hermes:** "Funnel enrolled, lesson_1_done, lesson_3_done, final_quiz_passed, by monthly cohort."
- **What you get:** the lesson where learners leave, and whether the October cohort (with the new welcome video) does better.

### 3. Newsletter engagement beyond opens
- **Ask Hermes:** "Treat only clicks and replies as active. Who is really engaged over 8 weeks?"
- **What you get:** stickiness on real actions, cohorts by sign-up week, and a list size of truly engaged readers (opens are inflated by privacy features of mail apps).

## Limits

- Weekly cohorts by first event; for monthly products, aggregate differently or extend `--weeks`.
- Funnel steps must happen in order; it does not handle time limits between steps.
- Correlation is not causation: a better cohort may come from a different channel, not your change. Use `engagement-booster` with an A/B test to prove an effect.

## Testing

`tests/test_ai_workforce.py` runs the bundled events and checks funnel counts, stickiness bounds and cohort shape. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`engagement-booster` (test fixes), `journey-personalizer` (target the segments that drop), `data-visualizer` (retention and funnel charts), `trend-watcher` (what users say while they leave).
