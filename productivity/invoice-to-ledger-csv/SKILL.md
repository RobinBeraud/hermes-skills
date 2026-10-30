---
name: invoice-to-ledger-csv
description: Extract supplier, date, net, VAT, gross and a suggested category from invoice text or PDF files into an accounting-ready CSV, with total-consistency checks. Use when you have a batch of invoices to enter in a ledger or spreadsheet.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [invoice, accounting, csv, vat, bookkeeping]
    category: productivity
    requires_toolsets: [terminal]
---

# Invoice to ledger CSV

Turns invoices (plain text, or PDFs with a text layer) into one CSV row each: supplier, invoice number, date, currency, net, VAT, VAT rate, gross, proposed category, status and warnings. Every row is checked (net + VAT = gross, stated rate vs computed rate) and anything doubtful is flagged `REVIEW` instead of being silently accepted.

## When to use

- You received several supplier invoices and want them in a spreadsheet or bookkeeping import.
- You want a quick sanity check that the totals on an invoice add up.
- You want a first-pass expense category that you can then correct.

Not a substitute for an accountant: categories are keyword guesses, and the script does no tax advice.

## Requirements

- Python 3.8+ (standard library only).
- For `.pdf` input: the `pdftotext` binary (package `poppler-utils`). Without it, PDF files get an `ERROR` row; convert them to `.txt` yourself.
- Scanned PDFs without a text layer are not supported (OCR them first).
- No API key, no network access.

## Usage

The script is `scripts/invoice_to_ledger.py` (path relative to this skill folder).

```bash
# 1. Self-test with built-in sample invoices
python3 scripts/invoice_to_ledger.py --selftest

# 2. Several invoices to a CSV file
python3 scripts/invoice_to_ledger.py inv1.txt inv2.pdf -o ledger.csv

# 3. From stdin, semicolon delimiter (spreadsheets in French locales)
cat inv.txt | python3 scripts/invoice_to_ledger.py - --delimiter ';'

# 4. Your own categories: JSON {"Category": ["keyword", ...]}
python3 scripts/invoice_to_ledger.py inv.txt --rules my_rules.json

# 5. Looser total check (default 0.02 per invoice)
python3 scripts/invoice_to_ledger.py inv.txt --tolerance 0.05
```

Exit code is 0 when every row is `OK`, 1 when at least one row needs review (a summary goes to stderr).

Recognised input: English and French labels (Subtotal / Total HT, VAT / TVA, Total due / Total TTC), amounts like `1 234,56`, `1,234.56`, `1.234,56`, dates like `14/03/2026` (day first), `2026-03-14`, `March 5, 2026`, `3 mars 2026`, currencies `€ $ £` and `EUR USD GBP CHF`.

Workflow for an agent: run the script, open the CSV, resolve every `REVIEW` row by reading the original invoice, correct the category column, and only then import.

## Example output

```
file,supplier,invoice_number,date,currency,net,vat,vat_rate_pct,gross,category,status,warnings
fr.txt,ACME Hébergement SARL,FA-2026-0042,2026-03-14,EUR,1000.00,200.00,20,1200.00,Software & subscriptions,OK,
bad.txt,Initech Print,55-A,2026-02-01,,100.00,20.00,20,130.00,Marketing & advertising,REVIEW,totals mismatch: net 100.00 + vat 20.00 = 120.00 != gross 130.00
```

## Limits

- Heuristics on text lines: invoices with multi-column layouts, several VAT rates, or line-item tables whose labels look like totals can give wrong figures. Always check `REVIEW` rows and spot-check `OK` rows.
- Only one VAT amount per invoice (the last matching line); mixed-rate invoices will probably be flagged.
- Day-first dates are assumed for numeric formats (`03/04/2026` is 3 April).
- Supplier is the first plausible header line, which may be a logo text or the wrong party.
- Categories are simple keyword counts; unmatched invoices are `Uncategorised`.
- Tested only on plain-text samples. PDF extraction through `pdftotext` is implemented but **untested** here (the binary was not installed on the test machine). Status for PDF input: untested.

## Testing

Run `python3 scripts/invoice_to_ledger.py --selftest`; it must print `selftest OK`. It checks French and English samples, amount parsing in three formats, category suggestion and detection of a deliberately inconsistent total.

Tested on Hermes v0.22.5 on 2026-10-30 (text input and self-test only; PDF input not exercised).
