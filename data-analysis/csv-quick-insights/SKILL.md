---
name: csv-quick-insights
description: Profile an unfamiliar CSV in seconds with a stdlib-only Python script: column types, missing values, duplicates, numeric outliers, top categories and three text charts. Use before cleaning or analysing any CSV export.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [csv, data-quality, profiling, analysis, stdlib]
    category: data-analysis
    requires_toolsets: [terminal]
---

# CSV Quick Insights

A single-file profiler that tells you what is inside a CSV before you start working with it.

## When to use

- You received a CSV or spreadsheet export and want to know its shape and quality fast.
- You need to spot empty columns, duplicate rows, ragged lines or suspicious values before importing the data somewhere.
- You want a quick summary to paste into a report or a chat.

## Requirements

- Python 3.8+ (standard library only, no pip install, no API key).
- A local CSV file (UTF-8, optionally with BOM). The delimiter (`,` `;` tab `|`) is auto-detected.

## Usage

The script lives in `scripts/csv_insights.py` inside this skill.

```bash
# Human-readable report
python3 scripts/csv_insights.py data.csv

# Force a delimiter
python3 scripts/csv_insights.py data.csv --delimiter ';'

# Only look at the first 10000 data rows
python3 scripts/csv_insights.py big.csv --max-rows 10000

# Machine-readable output
python3 scripts/csv_insights.py data.csv --json

# Built-in check
python3 scripts/csv_insights.py --selftest
```

What it reports:

1. Row and column counts, detected delimiter, duplicate rows, rows with the wrong number of fields.
2. Per column: inferred type (integer, float, date, boolean, category, text, empty), missing count and percentage, distinct count.
3. Numeric columns: min, median, mean, max and an outlier count using the 1.5 x IQR rule.
4. Categorical columns: the most frequent values.
5. Three text charts: missing values per column, a histogram of the first numeric column (columns named `id` or `index` are skipped), and top values of the first categorical column.

After running it, summarise the findings for the user and suggest concrete next steps (drop empty columns, deduplicate, investigate outliers). Treat outliers as things to check, not as errors.

## Example output

```
Rows: 8  Columns: 6  Delimiter: ,
Duplicate rows: 1  Rows with wrong field count: 0

Columns
- id [integer] missing=0 (0.0%) distinct=7 min=1 median=4.5 mean=4.375 max=7 outliers=0
- city [category] missing=0 (0.0%) distinct=3 top=Paris:5, Lyon:2, Nice:1
- price [integer] missing=2 (25.0%) distinct=6 min=95 median=102.5 mean=418 max=2000 outliers=1
- signup [date] missing=0 (0.0%) distinct=7
- active [boolean] missing=0 (0.0%) distinct=2 top=yes:6, no:2
- note [category] missing=5 (62.5%) distinct=2 top=ok:2, fine:1
```

## Limits

- The whole file is read into memory; use `--max-rows` for very large files.
- Type inference is heuristic: a column of numeric codes (zip codes, phone numbers) will be reported as integer, and the "category" threshold (at most 10 distinct values, or 20% of rows) is arbitrary.
- Dates are only recognised as `YYYY-MM-DD` (optionally with time) or `DD/MM/YYYY`.
- Numbers with a decimal comma (`1,5`) are not parsed as floats.
- Missing markers are: empty, NA, N/A, NaN, null, none, `-`, `?` (case-insensitive).
- Charts are plain text, not images. No encoding detection beyond UTF-8 (invalid bytes are replaced).

## Testing

Run `python3 scripts/csv_insights.py --selftest`; it prints a sample report and `SELFTEST OK` if the assertions on types, duplicates, outliers and delimiter detection pass. A semicolon-delimited file and `--json` output were also checked manually.

Tested on Hermes (cron agent run) on 2026-11-03.
