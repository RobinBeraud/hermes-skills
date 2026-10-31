---
name: flip-margin-calculator
description: Compute the projected profit, margins, ROI, break-even resale price and sensitivity table of a buy-renovate-resell property deal from editable assumptions; use it to sanity-check a flip before committing.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [real-estate, finance, flipping, margin, calculator]
    category: finance
    requires_toolsets: [terminal]
---

# Flip Margin Calculator

A small, offline Python script that turns a handful of deal assumptions into a transparent cost breakdown and a projected margin for a property flip (buy, renovate, resell).

## When to use
- You are evaluating a property to buy, renovate and resell, and want a quick margin estimate.
- You want to know the maximum purchase price that still leaves a target margin.
- You want to see how a lower resale price or a works overrun would hit the profit.

## Requirements
- Python 3.8+ (standard library only). No API key, no network.
- Script: `scripts/flip_margin.py` inside this skill folder.

## Usage

Inline parameters (any amount is in your own currency):

```bash
python3 scripts/flip_margin.py \
  --purchase-price 180000 --resale-price 280000 \
  --works-budget 35000 --holding-months 8 \
  --monthly-carrying-costs 400 \
  --loan-ltc-pct 80 --loan-rate-pct 4 --loan-fees 1500 \
  --target-margin 15
```

Or from a JSON file (keys use underscores, e.g. `purchase_price`):

```bash
cat > /tmp/deal.json <<'JSON'
{"purchase_price": 180000, "resale_price": 280000, "works_budget": 35000,
 "holding_months": 8, "loan_ltc_pct": 80}
JSON
python3 scripts/flip_margin.py --config /tmp/deal.json --target-margin 15
```

Parameters (all editable): `purchase_price`, `resale_price` (required); `works_budget`, `works_contingency_pct`, `acquisition_fees_pct`, `other_acquisition_costs`, `holding_months`, `monthly_carrying_costs`, `resale_fees_pct`, `loan_ltc_pct`, `loan_rate_pct`, `loan_fees`, `loan_type` (`interest_only` or `amortizing`), `loan_term_months`. Add `--json` for machine-readable output.

Defaults for contingency (10%), acquisition fees (7.5%), resale fees (4%) and loan rate (4%) are placeholders only. The report prints every assumption so they are never hidden. Replace them with figures valid for your country and deal. When using this skill for a user, always ask for or confirm these values rather than silently relying on the defaults.

## Example output

```
COSTS
  purchase price            180,000
  works (with contingency)  38,500
  acquisition costs         13,500
  carrying costs            3,200
  loan interest + fees      6,161
  resale fees               11,200
  TOTAL COST                252,561

RESULT (before any tax)
  net profit                27,439
  margin on resale price    9.8%
  equity invested           66,561
  break-even resale price   251,418
  max purchase price for 15% margin on resale: 166,718
```

## Limits
- Profit is shown before any tax; this skill gives no tax, legal or investment advice.
- Equity is a simplification: all costs are treated as funded up front, and the loan is repaid in full at resale.
- The loan covers a percentage of purchase plus works only; staged drawdowns are not modelled.
- Interest is charged per whole month (rounded up); no inflation, discounting or price-change model.
- Output is only as reliable as the inputs; the tool does not look up market prices or local fees.

## Testing
- `python3 scripts/flip_margin.py --selftest` checks profit arithmetic, interest, break-even, the purchase-price solver, amortizing vs interest-only and input validation. Expected last line: `selftest OK`.
- Tested on Hermes (terminal toolset) on 2026-10-31: selftest passed and the example above was run as shown.
