---
name: creator-analytics-digest
description: Turn a CSV export of post or video statistics (YouTube Studio, Instagram, TikTok, LinkedIn, any spreadsheet) into a plain-language digest of what worked, what did not, the trend, and follow-up content ideas. Use when a creator asks "what is working on my channel?".
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [analytics, creators, csv, youtube, instagram, tiktok, linkedin]
    category: data-analysis
    requires_toolsets: [terminal]
---

# Creator Analytics Digest

Reads an analytics export with one row per post or video, computes the facts with a small script, then the agent explains them in plain language and proposes next content ideas grounded in those facts.

## When to use

- The user shares a CSV exported from a platform dashboard and wants to know which content performs, whether things are improving, and what to make next.
- A weekly or monthly review of a channel, newsletter or social account.
- Do NOT use it to predict future growth or to compare accounts of very different sizes.

## Requirements

- Python 3 (standard library only). No API key, no network access.
- A CSV file (comma, semicolon or tab separated; UTF-8). Most dashboards offer "Export" or "Download data" as CSV. If you only have a spreadsheet, save it as CSV first.

## Usage

1. Ask the user which metric matters most (views, watch time, saves, clicks...). If they have no preference, let the script auto-detect.
2. Run the script (`SKILL_DIR` is the folder of this skill):

```bash
python3 SKILL_DIR/scripts/digest.py export.csv
python3 SKILL_DIR/scripts/digest.py export.csv --metric "Impressions" --top 5
python3 SKILL_DIR/scripts/digest.py export.csv --metric Views --title "Video title" --date "Publish date"
```

   The script finds the title, date and metric columns by name (English, French and Spanish headers are recognised). If it cannot, it lists the columns; rerun with `--metric`, `--title`, `--date`.
3. Read the output and write the digest for the user, in this order:
   - **What worked**: the best items and any standout (at least twice the median). Quote the exact title and number from the output.
   - **What lagged**: the weakest items, without blaming the creator.
   - **Trend**: first-half versus second-half median, only if the dates were found.
   - **Hypotheses, not facts**: for each standout, offer one or two possible reasons based only on what is visible (title wording, topic, format, day of week). Label them as guesses.
   - **Three follow-up ideas**: sequels or variations of the standouts, each tied to the row it came from.
   - **Data caveats**: how many rows were used and skipped, and whether the sample is small.
4. Never claim causes the data cannot show (the export has no audience or thumbnail information). Never invent numbers; if the user asks for something the CSV does not contain, say so.

Notes for the agent:
- Summary rows ("Total", "Overall") are skipped automatically.
- Percentages such as `4.1%`, thousands separators (`1,200`) and `2.4K` are understood.
- Weekday figures use few posts each: present them as hints only.
- With fewer than 4 usable rows the script stops: tell the user there is too little data.

## Example output

Test data with seven fictional videos (see `--selftest`):

```
# Analytics digest

Metric: **Views** | rows used: 7 (skipped: 1)
Median: 1,500 | mean: 1,771 | total: 12,400

## Best
- Sweater pattern: 3,500 (line 5)
- Q&A: 2,400 (line 8)

## Standouts (at least 2x the median)
- Sweater pattern: 3,500

## Trend (2026-01-05 to 2026-02-16)
- Median of first half: 1,100, second half: 2,100, change: +91%
```

The agent then writes: "Your sweater pattern video got more than twice your typical views. Guess: a concrete project in the title. Idea: a follow-up with a second pattern."

## Limits

- It describes one export; it does not explain why something worked.
- Small samples (a few dozen rows or fewer) give noisy medians and weekday hints.
- Date parsing covers common formats (ISO, day/month/year, month/day/year, "Jan 5, 2026"); ambiguous `01/02/2026` is read as day/month first. Check the date column if the trend looks odd.
- Only one metric is analysed per run; run again for another column.
- Tested only on small fictional files, not on real exports from every platform: column naming differs between dashboards.

## Testing

```bash
python3 SKILL_DIR/scripts/digest.py --selftest
```

Prints a sample digest and `SELFTEST OK`. Also checked with a semicolon-separated French-header file containing a "Total" row (the total was excluded).

Tested on Hermes v0.23.1 on 2026-11-18.
