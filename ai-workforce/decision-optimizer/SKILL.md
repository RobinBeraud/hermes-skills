---
name: decision-optimizer
description: Choose between options with weighted criteria, hard constraints and a sensitivity test that shows whether the winner survives a change of weights, using a dependency-free Python script. Use for vendor, tool, hire, location or roadmap choices when you want a transparent decision instead of the loudest opinion.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [decision-making, multi-criteria, prioritization, vendor-selection, sensitivity-analysis, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [idea-generator, digital-simulation, research-assistant, product-critic]
---

# Decision Optimizer

The Decision Optimizer finds the best option by evaluating several variables at once, and tells you how fragile that answer is. Options that break a hard constraint (budget, legal, deadline) are removed first. The rest are scored on normalised criteria, then every weight is moved up and down to see whether the winner changes.

## When to use

- Choosing a vendor, a tool, a candidate shortlist, a city for an office, a feature to build next.
- A committee is split and you want the trade-offs on the table.
- You must document why a choice was made (procurement, audit, board).

## How the agent works

1. **Frame the decision:** the question, the options (3 to 8), who decides, and the deadline.
2. **Separate musts from wants.** Musts become `constraints` (min/max). Wants become `criteria` with a direction (higher or lower is better) and a weight from 1 to 5. The agent asks the decision owner for weights before seeing the scores, to avoid fitting weights to a favourite.
3. **Collect values** for each option, citing the source (quote, demo, reference call). Unknowns are estimated and marked.
4. **Run the script.** Read the ranking, the contribution of each criterion, the excluded options and the sensitivity result.
5. **Recommend** in four lines: the winner, the margin, what would have to be true for the runner-up to win, and the main risk of the winner with a mitigation.

## Usage

```bash
python3 scripts/decide.py examples/crm_choice.json
python3 scripts/decide.py decision.json --json
```

Example output on the bundled CRM choice:

```
| Rank | Option | Score | annual_cost_eur | ease_of_use | integrations | migration_weeks | gdpr_eu_hosting |
|---|---|---|---|---|---|---|---|
| 1 | CRM Alpha | 0.638 | 0.120 | 0.286 | 0.054 | 0.107 | 0.071 |
| 2 | CRM Beta | 0.429 | 0.000 | 0.143 | 0.214 | 0.000 | 0.071 |
| 3 | CRM Gamma | 0.429 | 0.214 | 0.000 | 0.000 | 0.143 | 0.071 |
Excluded: CRM Delta (annual_cost_eur 21000 > max 15000; gdpr_eu_hosting 0 < min 1)

Winner: CRM Alpha, margin 0.209
Robust to +/-50% on any single weight.
Closest flip: raising 'integrations' weight by 140% makes CRM Beta win
```

## Documented use cases

### 1. Selecting a SaaS vendor
- **Ask Hermes:** "decision-optimizer: compare these 4 e-signature tools. Must: EU hosting, under 3k/year. Wants: API quality, ease of use, templates."
- **What you get:** the ranking, excluded vendors with the reason, and a recommendation memo that procurement can file.

### 2. What to build next quarter
- **Ask Hermes:** "Score these 7 roadmap items on customer value, revenue impact, effort (lower is better) and strategic fit. Team capacity is 3 items."
- **What you get:** a ranked list with the top 3, and the items whose position depends on one weight (the ones to discuss in the meeting).

### 3. Choosing a training venue
- **Ask Hermes:** "Three venues for a 2-day workshop: price, access by train, room quality, catering. Must: 20 seats, accessible to wheelchairs."
- **What you get:** the choice, the margin and a note that the decision flips if access by train is weighted much higher.

## Limits

- A weighted sum assumes criteria can compensate each other (a cheap option can make up for a weak one). For true deal-breakers, use constraints.
- Min-max normalisation is relative to the options on the table; adding an option can change scores.
- Garbage in, garbage out: the script makes the reasoning visible, it does not check that values are right.

## Testing

`tests/test_ai_workforce.py` checks constraints exclude the right option, the ranking on the bundled file and the sensitivity output. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`idea-generator` to widen the options first, `research-assistant` to source the values, `digital-simulation` when values are uncertain ranges, `product-critic` to challenge the winner.
