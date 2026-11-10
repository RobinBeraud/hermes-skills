---
name: engagement-booster
description: Design and prove engagement improvements: diagnose the drop-off, pick behaviour-based interventions (nudges, timing, rewards, social proof, friction removal), adapt them to how users behave, and size and read the A/B test with a dependency-free Python script. Use when you want more people to come back or finish, without dark patterns.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [engagement, growth, ab-testing, experimentation, behavioral-design, retention, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [engagement-assessor, journey-personalizer, content-creator]
---

# Engagement Booster

The Engagement Booster creates adaptive experiences based on user behaviour, and proves they work. It starts from where people drop (measured by `engagement-assessor`), proposes small changes grounded in behavioural design, adapts them to segments, and runs them as experiments with a sample size decided in advance. A change only ships as a win if the numbers say so.

## When to use

- Users sign up but do not reach the "aha" moment, or come once and never again.
- Course learners stop at lesson 2, newsletter readers stop clicking, community members lurk.
- Someone wants to "add gamification" and you want to test whether it helps.

## How the agent works

1. **Diagnose the moment that matters:** the step with the biggest drop or the behaviour that predicts retention (for example "users who invite a teammate in week 1 stay 3 times longer").
2. **Map the behaviour** with a simple model: is it motivation (why bother), ability (too hard, too long) or a missing prompt (nobody reminds them at the right time)?
3. **Pick interventions** to match: remove friction (fewer fields, templates, defaults), better timing (reminder when the user is usually active), progress and goals, social proof that is true, small rewards tied to real value. One change per test.
4. **Adapt** by segment: new vs returning, mobile vs desktop, behaviour in the last 7 days. Hand rules to `journey-personalizer`.
5. **Size the test** before starting (`abtest.py size`), run whole weeks, then read it once at the planned end (`abtest.py read`).
6. **Decide:** ship, iterate or drop, and record the learning, including the tests that did not work.

## Usage

```bash
# How long must the test run?
python3 scripts/abtest.py size --baseline 0.12 --mde 0.02 --daily-traffic 800
# Read the result at the planned end
python3 scripts/abtest.py read --control 2400,288 --variant 2380,345
```

Example output:

```
Baseline 12.0%, detect +2.0% absolute (to 14.0%), alpha 0.05, power 80%
Needed: 4,438 visitors per variant, 8,876 in total.
At 800 visitors/day: 12 days. Run whole weeks: 14 days.

Control 12.00% (288/2400) vs variant 14.50% (345/2380)
Lift +2.50 pts (+20.8%), 95% CI +0.57 to +4.42 pts, p = 0.0109
Verdict: the variant wins at the 95% level, if the sample size was fixed in advance.
```

## Documented use cases

### 1. Activation of a SaaS trial
- **Ask Hermes:** "engagement-booster: only 47% of users who create a project invite a teammate. Propose 3 tests and size them for 800 sign-ups a week."
- **What you get:** three single-change tests (invite prompt right after the first success, a pre-filled invite message, a shared template that needs a teammate), with the expected effect, the test length for each and the stop rule.

### 2. Course completion
- **Ask Hermes:** "Learners drop after lesson 2. What could help, and how do we know?"
- **What you get:** a diagnosis (lesson 3 is 40 minutes long: ability problem), interventions (split it, show "12 minutes left", a check-in message from the trainer on day 3), and an A/B plan by cohort.

### 3. Newsletter re-engagement
- **Ask Hermes:** "Design a re-engagement sequence for readers who have not clicked in 90 days, and measure it."
- **What you get:** a 3-e-mail sequence with one clear value each, a holdout group to measure the true effect, and the rule to unsubscribe those who still do not engage (good for deliverability).

## Guardrails and limits

- No dark patterns: no fake scarcity, no fake social proof, no hidden unsubscribe, no guilt-tripping copy, no streaks designed to create anxiety. Engagement must serve the user's goal.
- Respect consent and privacy rules for behavioural targeting (GDPR, ePrivacy).
- Do not peek and stop early when the result looks good; the p-value is only valid at the planned sample size.
- Small audiences cannot detect small effects: the size step tells you when a test is not worth running.

## Testing

`tests/test_ai_workforce.py` checks sample sizes against the textbook formula and the verdicts on clear, null and tiny-sample cases. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`engagement-assessor` (diagnose and measure), `journey-personalizer` (deliver the variant to the right users), `content-creator` (write the nudges).
