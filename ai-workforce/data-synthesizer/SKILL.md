---
name: data-synthesizer
description: Generate realistic, reproducible synthetic datasets for testing, demos and training from a JSON schema, or infer a privacy-safe schema from a real CSV without copying its values, with a dependency-free Python script. Use when you need data that looks real but contains no real person.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [synthetic-data, test-data, privacy, gdpr, csv, demo, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [data-visualizer, data-forecaster, content-guardian]
---

# Data Synthesizer

The Data Synthesizer creates datasets for training, testing and demos. It is deterministic (same seed, same rows), keeps realistic distributions and relationships between columns, and never puts a real customer into a test environment. In `profile` mode it learns the shape of a real CSV (types, ranges, frequencies) while dropping free text and rare values, so the synthetic copy cannot leak individuals.

## When to use

- A demo, a staging environment or a workshop needs believable data.
- A test suite needs edge cases: nulls, extreme values, skewed categories.
- Someone suggests "just copy production": give them a synthetic twin instead.
- You train or evaluate a model and need labelled examples in quantity.

## How the agent works

1. **Agree on the use:** demo (pretty and plausible), testing (edge cases on purpose), or training (realistic distributions). Ask for row count and any rule that must hold.
2. **Write or infer the schema.** From a description, write `schema.json`. From a real file, run `profile` and review the inferred schema with the user (rename sensitive columns, tune ranges).
3. **Add realism:** weights for categories, `depends_on` for correlated numbers (spend grows with age), `null_rate` for missing data, dates in a window.
4. **Generate** with a fixed seed and commit the schema, not the data: anyone can regenerate the same file.
5. **Check** the output: open the first rows, run `csv-quick-insights` or chart a column, and confirm the business rules.

## Usage

```bash
# Generate from a schema (200 rows, seed 7, as defined in the schema)
python3 scripts/synth.py generate examples/customers.schema.json --out customers.csv

# Override size or seed
python3 scripts/synth.py generate examples/customers.schema.json --rows 5000 --seed 2027 --out big.csv

# Learn the shape of a real export, without copying names, e-mails or free text
python3 scripts/synth.py profile export_crm.csv --min-count 5 --out crm.schema.json
```

Column types: `id`, `int`, `float`, `choice`, `bool`, `date`, `name`, `email` (always `@example.com`), `text`. Options: `min`, `max`, `mean`, `sd`, `decimals`, `values` with weights, `p`, `start`/`end`, `null_rate`, `depends_on`.

Example output (first rows of `customers.csv`):

```
customer_id,full_name,email,country,age,monthly_spend,signup_date,plan,churned,last_feedback
C-1000,Adam Bernard,adam.bernard.1@example.com,ES,42,50.16,2026-07-19,pro,False,Report report slow
C-1001,Nora Rossi,nora.rossi.2@example.com,ES,39,38.31,2025-04-10,free,False,Team login report login great quality
```

## Documented use cases

### 1. A demo CRM for a sales training
- **Ask Hermes:** "data-synthesizer: 300 B2B leads for a CRM demo, French and Belgian companies, deal size skewed (many small, few big), 20% lost."
- **What you get:** a schema with weighted choices and a `deal_value` distribution, a CSV ready to import, and the seed to recreate it.

### 2. Staging without personal data (GDPR)
- **Context:** developers want production customers in staging.
- **Ask Hermes:** "Profile customers_export.csv and generate a synthetic twin of 10,000 rows."
- **What you get:** an inferred schema (names and free-text columns turned into synthetic types, categories under 5 occurrences grouped as OTHER), the generated file, and a note listing which columns were neutralised.

### 3. Edge cases for a test suite
- **Ask Hermes:** "Generate 50 orders with 10% missing addresses, quantities from 0 to 9999 and dates around the daylight saving change."
- **What you get:** a CSV hitting the boundaries on purpose, plus the list of cases it covers.

## Limits

- Correlations are simple (one linear `depends_on` per column). It does not reproduce complex joint distributions or time dynamics.
- `profile` keeps aggregate statistics; with very small files, even ranges can be revealing. Review the schema before sharing it.
- Generated names are a small fixed list; do not use them to test name-matching algorithms.

## Testing

`tests/test_ai_workforce.py` checks reproducibility (same seed, same output), ranges, null rates and that `profile` never copies free text. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`data-visualizer` to show the generated distributions, `engagement-assessor` and `data-forecaster` to rehearse an analysis on fake data first, `content-guardian` to confirm no real e-mail slipped in.
