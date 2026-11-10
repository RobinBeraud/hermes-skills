---
name: digital-simulation
description: Test scenarios on a virtual model before acting: describe inputs as ranges, outputs as formulas, and run a Monte Carlo simulation with a dependency-free Python script that reports P10/median/P90, the odds of hitting a target and one-factor what-ifs. Use for launches, budgets, capacity and pricing decisions under uncertainty.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [simulation, monte-carlo, what-if, scenario-planning, risk, forecasting, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [data-forecaster, decision-optimizer, digital-twin]
---

# Digital Simulation

The Digital Simulation agent tests scenarios through a virtual model instead of in real life. You describe what you know as ranges ("between 6,000 and 16,000 visitors, most likely 9,000"), how the result is computed, and the agent runs thousands of possible futures. The answer is a distribution: what usually happens, what happens in bad and good cases, and the probability of reaching your target.

## When to use

- "Will this launch break even?", "Can the team deliver by June?", "Do we need a second server?"
- A spreadsheet with single "best guess" numbers hides the risk and you want to see it.
- You want to compare scenarios: price A vs price B, one hire vs two.

## How the agent works

1. **Write the question and the decision rule** ("we launch if the probability of profit is above 70%").
2. **List inputs** and give each a range from data or from expert judgement: `triangular` for "low / most likely / high", `normal` for measured noise, `uniform` when only bounds are known, `choice` or `bernoulli` for events (a big client signs or not).
3. **Write outputs as formulas** of inputs and earlier outputs (`buyers = visitors * conversion`). Formulas are parsed safely: arithmetic, comparisons, `min`, `max`, `if_`.
4. **Run** 10,000 simulations, read P10, median, P90 and the target probabilities.
5. **Ask what-if** with `--set` (price=199) and check which inputs move the result most by fixing them one at a time at their low and high values.
6. **Report** in plain words with the assumptions listed, and warn about effects the model ignores (a higher price usually lowers conversion: model it if it matters).

## Usage

```bash
python3 scripts/simulate.py examples/launch_model.json
python3 scripts/simulate.py examples/launch_model.json --set price=199
python3 scripts/simulate.py model.json --runs 50000 --seed 7 --json
```

Example output on the bundled launch model:

```
10000 runs
Will the new online course break even in its first quarter?

| Output | P10 | Median | P90 | Mean | Target |
|---|---|---|---|---|---|
| buyers | 97.36 | 177.88 | 284.56 | 185.30 | above 150: 66% |
| net_revenue | 13,750.40 | 25,142.14 | 40,298.75 | 26,231.11 | - |
| profit | -4,034.82 | 7,544.03 | 22,833.79 | 8,575.13 | above 0: 79% |
```

With `--set price=199` the probability of profit rises to 91%, if conversion holds: the agent says so and suggests modelling conversion as a function of price.

## Documented use cases

### 1. Launch go/no-go
- **Ask Hermes:** "digital-simulation: will the new course break even? Visitors 6k to 16k, conversion 1.8% plus or minus 0.6, price 149, ads 9k, production 6k to 12k."
- **What you get:** the table above, the 79% probability of profit, the input that matters most (visitors), and the cheapest way to reduce that uncertainty (a pre-sale page).

### 2. Delivery date for a project
- **Ask Hermes:** "40 to 60 stories left, the team finishes 6 to 11 per sprint, 2-week sprints. When are we done at 85% confidence?"
- **What you get:** a model with `sprints = remaining / throughput`, the date at P50 and P85, and why a single date promise is a bet.

### 3. Server capacity
- **Ask Hermes:** "Peak users 800 to 2,500, each uses 30 to 60 MB, the server has 64 GB. Probability we run out of memory?"
- **What you get:** the probability, the peak memory at P90, and the what-if with 128 GB.

## Limits

- Inputs are independent unless you write the dependency in a formula.
- The model is only as good as its ranges: ask for ranges from data or from people who have done it before, and record the source.
- It is not a physics or discrete-event simulator (queues, agents moving in space). For those, use a dedicated tool.

## Testing

`tests/test_ai_workforce.py` checks reproducibility with a seed, the target probabilities on the bundled model, `--set`, and that unsafe formulas (imports, attributes) are refused. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`data-forecaster` (turn history into input ranges), `decision-optimizer` (choose between simulated scenarios), `digital-twin` (simulate changes on a live system model).
