---
name: real-estate-regulation-watch
description: Weekly watch on housing regulation news and French mortgage rates, built from public RSS feeds and the ECB open data API, with a source link on every line; use it to prepare a recurring housing-market briefing without legal or tax advice.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [real-estate, rss, watch, mortgage, regulation, digest]
    category: research
    requires_toolsets: [terminal]
---

# Real Estate Regulation Watch

Builds a short Markdown digest of recent housing and credit news from official public feeds, plus the latest monthly mortgage cost of borrowing in France. Every item carries its source URL. Nothing is interpreted as advice.

## When to use

- A weekly or monthly briefing on housing rules (rent, energy performance, renovation aid, property tax, urban planning) and on borrowing conditions.
- Scheduled runs where you only want items you have not seen before (state file).
- As raw material for a human or an agent that then reads the cited pages.

## Requirements

- Python 3.8+ (standard library only), outbound HTTPS access.
- No API key.

## Usage

The script is `scripts/regwatch.py`.

```bash
# Offline check, no network
python3 scripts/regwatch.py --selftest

# Last 7 days from the built-in feeds
python3 scripts/regwatch.py

# Last 30 days, with the last 6 monthly ECB mortgage rates for France
python3 scripts/regwatch.py --days 30 --rates 6

# Weekly cron style: only show what was not reported before
python3 scripts/regwatch.py --days 7 --rates 3 --state ~/.regwatch_state.json

# Add your own feed and keyword, machine-readable output
python3 scripts/regwatch.py --feed "my-source=https://example.com/feed.xml" --keyword "zoning" --json
```

Built-in sources (each returned RSS/CSV data when the skill was written):
- `https://www.economie.gouv.fr/rss/toutesactualites`
- `https://www.ecologie.gouv.fr/rss-actualites.xml`
- `https://www.ecb.europa.eu/rss/press.html`
- Rates: ECB series `MIR.M.FR.B.A2C.AM.R.A.2250.EUR.N` through `data-api.ecb.europa.eu`.

Use `--only-custom` to ignore the built-in feeds. Keywords are matched without accents and case; see `DEFAULT_KEYWORDS` in the script.

When summarizing the output for a user, quote the title and URL as printed, do not add legal or tax conclusions, and say that the rate is a market average.

## Example output

```
# Housing regulation and rates watch
Generated 2026-10-29 10:01 UTC, window: last 30 days.

## Mortgage cost of borrowing (France, ECB statistics)
- 2026-07: 3.18 % (+0.02 pt vs previous month)
- 2026-08: 3.20 % (+0.02 pt vs previous month)
...
## ECB press
- 2026-10-27 | October 2026 euro area bank lending survey | keywords: bank lending survey | https://www.ecb.europa.eu/...
Items: 3. Information watch only. This is not legal, tax or financial advice.
```

## Limits

- Keyword filtering is crude: expect some false positives (a generic article mentioning "logement") and misses. Tune keywords with `--keyword`.
- The general ministry feeds are not housing-specific; they only expose the most recent ~10-20 items, so a long gap between runs can lose items.
- Not covered because they blocked automated requests when tested: Legifrance, Banque de France, ACPR, vie-publique.fr. Add other feeds yourself with `--feed`.
- The ECB rate is an average of new loans reported by banks, published with a delay of about two months. It is not the usury rate and not an offer.
- A failing feed is reported on stderr and skipped; the run continues.
- No legal, tax or financial advice. Read the linked source.

## Testing

1. `python3 scripts/regwatch.py --selftest` must end with `SELFTEST OK` (parsing, filtering, state de-duplication, failing feed, rate deltas).
2. Live: `python3 scripts/regwatch.py --days 30 --rates 4 --state /tmp/st.json`, then run it again: the second run must report nothing new.

Status: tested (selftest and live run against the three feeds and the ECB API).
Tested on Hermes Agent on 2026-10-29.
