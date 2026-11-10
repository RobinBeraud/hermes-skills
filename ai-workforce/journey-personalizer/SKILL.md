---
name: journey-personalizer
description: Create customised user journeys from preferences and behaviour with explicit, auditable rules: segment users, assign each one a journey (message, channel, next best action), detect overlaps and empty rules before launch, and explain any single assignment, with a dependency-free Python script. Use for onboarding, nurturing, win-back and upsell flows.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [personalization, segmentation, customer-journey, crm, lifecycle-marketing, next-best-action, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [engagement-assessor, engagement-booster, content-creator, interactive-companion]
---

# Journey Personalizer

The Journey Personalizer creates customised experiences based on what users want and do. It keeps personalisation explainable: every user gets a journey through rules you can read, test and audit, written by the agent from your goals and data. Before anything is sent, the script shows how many people land in each journey, who matches several rules, which rules match nobody and who is excluded (opt-outs first).

## When to use

- One generic onboarding or newsletter for everyone, while users clearly differ.
- A CRM export and a goal ("bring back inactive buyers", "upsell growing teams") but no plan.
- You need to justify why a person received a message (customer service, GDPR right of access).

## How the agent works

1. **Start from goals,** one per journey: activate, retain, win back, upsell, refer. Each journey has a message, a channel and a success metric.
2. **Find the signals** in the data: plan, days since signup, usage, last seen, language, stated preferences. Use preferences people gave you before inferred ones.
3. **Write rules** in `rules.json`, most specific first (first match wins), with exclusions on top (opt-out, open support ticket, recent purchase).
4. **Dry-run** with `personalize.py`: check sizes, overlaps and empty rules. Fix the order or the thresholds until the split makes sense.
5. **Explain** any assignment with `--explain USER_ID` before a complaint arrives, then export the assignments CSV to the CRM or e-mail tool.
6. **Write the content** per journey with `content-creator`, and measure each journey against a holdout with `engagement-booster`.

## Usage

```bash
python3 scripts/personalize.py examples/users.csv examples/rules.json
python3 scripts/personalize.py examples/users.csv examples/rules.json --out assignments.csv
python3 scripts/personalize.py examples/users.csv examples/rules.json --explain u7
```

Example output on the bundled users:

```
300 users
  activation_rescue            67   22.3%
  win_back                    112   37.3%
  team_upsell                  23    7.7%
  enterprise_contact            0    0.0%   <- nobody matches: check the rule
  nurture                      80   26.7%
  EXCLUDED                     18    6.0%
  overlap: 24 user(s) match win_back + team_upsell -> only 'win_back' applies
  overlap: 15 user(s) match activation_rescue + team_upsell -> only 'activation_rescue' applies
```

Here the dry run shows two decisions to take: should growing pro teams get the upsell even if they are inactive (reorder the rules?), and the enterprise rule is useless with current data.

## Documented use cases

### 1. Onboarding by role
- **Ask Hermes:** "journey-personalizer: three onboarding paths for managers, individual contributors and admins, from the role they chose at sign-up, in their language."
- **What you get:** rules on `role` and `language`, a dry-run report, and per journey the first three messages to write.

### 2. Win-back for an online shop
- **Ask Hermes:** "Customers who bought twice or more but not in 120 days: offer the category they bought most. Exclude anyone with an open complaint."
- **What you get:** rules, the segment size per category, and the assignments CSV for the e-mail tool.

### 3. Training follow-up
- **Ask Hermes:** "After a course, send participants different resources depending on the quiz score and the topic they rated most useful."
- **What you get:** journeys "deepen", "practise" and "coach me", with the resource for each and the rule behind it.

## Limits

- Rules, not machine learning: transparent and controllable, but you choose the thresholds. Revisit them with data from `engagement-assessor`.
- Sensitive attributes (health, religion, political views, ethnicity) must not drive personalisation.
- The script assigns journeys; sending, consent and frequency capping belong to your e-mail or CRM tool.

## Testing

`tests/test_ai_workforce.py` checks first-match order, exclusions, overlap and empty-rule reporting on the bundled users. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`engagement-assessor` (find the segments), `engagement-booster` (test each journey), `content-creator` (write the messages), `interactive-companion` (personal guidance in conversation).
