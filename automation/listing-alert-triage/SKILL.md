---
name: listing-alert-triage
description: Parse real-estate listing alert e-mails (plain text, HTML or .eml), extract price, surface and city, compute price per m2, compare it to reference prices you provide and rank listings as GEM / watch / pass.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [real-estate, email, triage, price-per-m2, automation]
    category: automation
    requires_toolsets: [terminal]
---

# Listing Alert Triage

Property alert e-mails pile up fast and each one forces you to do the same mental arithmetic: price divided by surface, compared with what the area usually costs. This skill does it in bulk with a single standard-library Python script and ranks the listings by how far they sit below your own reference price per m2.

## When to use

- You receive alert e-mails from property portals and want the interesting ones surfaced first.
- You have exported alerts as `.eml` or `.txt` (or pasted the text) and want a ranked table, JSON or CSV.
- You want configurable "gem" criteria: ratio to reference, min/max surface, max price.

Not for: valuation, legal, tax or financing advice. The tool only does arithmetic on numbers found in the text.

## Requirements

- Python 3.8+, standard library only. No API key, no network access.
- Reference prices per m2 are **supplied by you** (from your own research); the script ships with none.

## Usage

Script: `scripts/triage.py` (inside this skill directory).

```bash
# One or several files; references on the command line (CITY=EUR_PER_M2, repeatable)
python3 scripts/triage.py alert1.eml alert2.txt \
  --ref Lyon=5000 --ref Bordeaux=4000 --ref default=3500

# References from a JSON file, extra criteria, CSV output
echo '{"Nantes": 3900, "Rennes": 3400}' > refs.json
python3 scripts/triage.py alerts/*.eml --ref-file refs.json \
  --min-area 25 --max-price 400000 --gem-ratio 0.85 --format csv

# From stdin
pbpaste | python3 scripts/triage.py - --ref Lille=3500 --format json
```

Options:
- `--gem-ratio` (default 0.85): price/m2 at most this fraction of the reference means GEM.
- `--watch-ratio` (default 0.97): at most this means `watch`; above means `pass`.
- `--suspect-ratio` (default 0.5): below this, the verdict gets a `?` suffix (e.g. `GEM?`) because a very low price is often an error, a scam or a major defect.
- `--min-area`, `--max-area`, `--max-price`: matching listings are `excluded`.
- `--format text|json|csv`, `--selftest`.

City matching ignores case and accents. `default=` is used when a city has no reference. Without any reference the verdict is `no-reference` but price/m2 is still computed.

Typical agent workflow: fetch the alert mails with your mail tool, save them as `.eml`/`.txt` in a temp folder, run the script with the user's reference prices and criteria, then report the GEM and `GEM?` lines with their links.

## Example output

```
[watch       ] Nantes           168 000 EUR      48 m2   3 500 EUR/m2  ref 3900.0  ratio 0.90x
    -> slightly below/near reference
    https://example.com/ad/2001
[excluded    ] Rennes           410 000 EUR     120 m2   3 417 EUR/m2  ref 3400.0  ratio 1.00x
    -> over max price
    https://example.com/ad/2002
```

## Limits

- Extraction is heuristic: it looks for an amount followed by `€`/`EUR` and a number followed by `m²`/`m2`, within one block separated by blank lines or `---` lines. Alert layouts vary; always spot-check the first run against the original e-mail.
- Only euro prices and square metres are understood. Rent vs sale is not distinguished; filter with `--max-price` or feed sale alerts only.
- City detection handles `City 12345`, `12345 City` and `in/à City`. Otherwise the city is `?` and `default=` applies.
- Identical listings (same price, surface, city) are deduplicated, which can merge two genuinely different but identical-looking units.
- Reference prices quality drives the result. A ratio is a screening signal, not a valuation.
- Tested only on synthetic fixtures, not on live portal e-mails.

## Testing

```bash
python3 scripts/triage.py --selftest      # prints ranked sample and "SELFTEST OK"
python3 scripts/triage.py examples/sample_alert.txt --ref Nantes=3900 --ref Rennes=3400
```

The self-test covers French/English price formats, duplicates, min-surface exclusion, suspicious-price flag and city detection. The sample file is raw MIME source (quoted-printable HTML with links); it is parsed correctly when saved with a `.eml` extension, e.g. `cp examples/sample_alert.txt /tmp/a.eml`.

Tested on Hermes v0.22.5 on 2026-10-27 (self-test and sample message copied to `.eml`, synthetic data only).
