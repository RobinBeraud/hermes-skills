---
name: area-market-analysis
description: Analyse the residential property market of a French commune from open DVF sales data (volumes, median price per m2, apartments vs houses, trend over years); use it when you need a sourced local market snapshot without any API key.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [real-estate, france, dvf, open-data, market-analysis]
    category: data-analysis
    requires_toolsets: [terminal]
---

# Area Market Analysis (France, open DVF data)

Builds a local property market snapshot for a French commune from the public "geolocated land value requests" dataset (DVF, published on data.gouv.fr). It downloads the commune's yearly CSV files, groups rows by sale, keeps clean single-dwelling sales, and reports volumes and median price per m2 per year.

## When to use

- You need a quick, sourced answer to "what do apartments and houses actually sell for in town X, and is it moving?"
- You are comparing several communes before a purchase, a pricing decision or a market note.
- You want numbers from recorded sales, not from listing asking prices.

Not for: valuing one specific property, legal or tax advice, or areas outside metropolitan France and the overseas departments covered by DVF (Alsace-Moselle and Mayotte are, to my knowledge, not covered by DVF; not verified).

## Requirements

- Python 3.8+ (standard library only), internet access.
- No API key. Endpoints used:
  - `https://geo.api.gouv.fr/communes` to resolve a commune name to its INSEE code.
  - `https://files.data.gouv.fr/geo-dvf/latest/csv/<year>/communes/<dept>/<insee>.csv` for the sales data.
- Files are cached in `/tmp/dvf_cache` (override with the `DVF_CACHE` environment variable).

## Usage

The script lives in `scripts/dvf_area.py` inside this skill.

```bash
# By name (the best match by population is used; other matches are listed on stderr)
python3 scripts/dvf_area.py --commune Bordeaux --years 2021-2024

# By INSEE code (unambiguous, recommended for scripting)
python3 scripts/dvf_area.py --insee 33063 --years 2022,2024

# Machine-readable output
python3 scripts/dvf_area.py --insee 33063 --years 2021-2024 --json

# Analyse a CSV you already downloaded
python3 scripts/dvf_area.py --file my_dvf.csv --label "Sample"

# Tighten or loosen the outlier filter (EUR per m2)
python3 scripts/dvf_area.py --insee 33063 --min-ppm2 1000 --max-ppm2 20000
```

Method, so you can explain the numbers:

1. Only rows with nature "Vente" are kept (exchanges, auctions, etc. are dropped).
2. Rows are grouped by sale id. Duplicate rows of the same dwelling (one per parcel) are collapsed.
3. A sale with exactly one apartment or one house becomes a price-per-m2 data point: sale value divided by built surface. Sales with several dwellings, with commercial premises, or with land only are counted in the volume but not in the price statistics.
4. Prices outside the min/max EUR/m2 bounds are dropped as probable data errors (counted in the JSON output as `outliers_excluded`).
5. Paris, Lyon and Marseille are automatically expanded to their arrondissements, because the dataset is split that way.

When reporting to a user, always cite the source (DVF geolocated, data.gouv.fr open data), the years, and the number of observations behind each median.

## Example output

Real run on 2026-10-28 (figures come from the dataset as downloaded that day):

```
Area: Bordeaux (33063)
Source: DVF geolocated (data.gouv.fr), sales ('Vente') only, outliers filtered

Year     Sales | Apartments (n / median EUR/m2 / IQR) | Houses (n / median EUR/m2 / IQR)
2021      6811 | 3950 / 4598 / 3816-5486            | 1473 / 5217 / 4397-6250
2022      6866 | 4120 / 4621 / 3862-5551            | 1379 / 5396 / 4545-6425
2023      5476 | 3262 / 4533 / 3737-5400            | 1039 / 5361 / 4444-6349
2024      4821 | 2844 / 4222 / 3517-5000            | 861 / 4955 / 4049-5923

Change 2021 -> 2024 (median EUR/m2, indicative, mix effects not removed):
  Apartments: -8.2%
  Houses: -5.0%
  Sales volume: -29.2%
```

## Limits

- Median price per m2 is a rough indicator. It does not control for condition, floor, parking, new vs old, or the micro-location inside the commune. Changes between years include a mix effect.
- Sales are registered with a delay and the most recent year may be incomplete; check the number of observations before reading a trend.
- The sale value can include movable goods or bundled lots that the dataset does not separate; the outlier filter removes only the extremes.
- A commune is a coarse area. For a neighbourhood you would need to filter by address or parcel, which this script does not do.
- Years available upstream at the time of writing: 2021 to 2025. The script reports and skips years with no file.
- Not legal, tax or valuation advice.

## Testing

```bash
python3 scripts/dvf_area.py --selftest      # offline, checks classification and medians on a tiny synthetic CSV
python3 scripts/dvf_area.py --commune Bordeaux --years 2023-2024   # live run
```

Status: tested. The self-test passed and live runs for Bordeaux (2021-2024) and Lyon (2023-2024, arrondissement expansion) returned data. Overseas communes, Corsica codes (2A/2B) and years other than those shown were not tested.

Tested on Hermes v0.22.5 on 2026-10-28.
