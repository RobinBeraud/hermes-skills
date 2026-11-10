---
name: data-visualizer
description: Turn a CSV or a table into a clear, accessible SVG chart whose title states the insight, with a dependency-free Python script (line, bar, horizontal bar, highlight, direct labels). Use when numbers need to be understood in five seconds in a report, newsletter, slide or post.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dataviz, charts, svg, reporting, accessibility, csv, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [data-forecaster, engagement-assessor, anomaly-detector]
---

# Data Visualizer

The Data Visualizer turns complex data into one picture with one message. It picks the chart from the question being asked, writes the insight as the title, highlights the point that matters and greys out the context. The bundled script renders the SVG with no plotting library, so it runs on any server where Hermes runs.

## When to use

- A weekly report, newsletter or slide needs a chart that does not need explaining.
- You have a CSV export and want to see the shape of the data before analysing it.
- You need a chart that screen readers can describe (the SVG carries a `<title>` and a `<desc>` with the values).

## How the agent works

1. **Question first.** What should the reader conclude? Change over time → line. Comparison of a few categories → bar. Ranking of many labelled items → horizontal bar, sorted. Part of a whole with 2 or 3 parts → a sentence or a stacked bar, never a 3D pie.
2. **Prepare the table.** Aggregate to the right grain (week, month), keep 12 to 24 points for a time series, 10 bars at most for a ranking (group the rest as "Other").
3. **Write the title as the takeaway** ("June's launch doubled signups"), the subtitle as the definition (metric, unit, period, source).
4. **Render** with `scripts/chart.py`, highlight the key point with `--highlight`, then look at the result and fix what misleads (cropped axis on bars, too many series, unreadable labels).
5. **Deliver** the SVG plus two sentences of interpretation and one caveat about the data.

## Usage

```bash
# Line chart, two series labelled at the end of each line, one highlighted month
python3 scripts/chart.py examples/signups.csv --x month --y signups,paid \
  --title "June's launch doubled signups, and paid users followed" \
  --subtitle "Monthly signups and new paid accounts, 2026" --highlight 2026-06 --out signups.svg

# Ranking: horizontal bars sorted, one channel highlighted, the others grey
python3 scripts/chart.py examples/channels.csv --x channel --y leads --type hbar --sort \
  --highlight Newsletter --title "The newsletter brings more leads than any other channel" --out channels.svg

# Simple bars with the record month labelled
python3 scripts/chart.py examples/signups.csv --x month --y signups --type bar --highlight 2026-06 --title "June was the record month"
```

Options: `--type line|bar|hbar`, `--unit EUR`, `--width`, `--height`, `--sort` (hbar). Bars always start at zero. The palette is colour-blind safe; with `--highlight`, single-series charts show the highlighted point in colour and the rest in grey.

## Documented use cases

### 1. Monthly business review
- **Ask Hermes:** "data-visualizer: from sales.csv make the chart for the board: monthly revenue 2026, highlight October, title with the takeaway."
- **What you get:** `revenue.svg`, the takeaway as title ("October beat the previous record by 12%"), and a caveat ("October includes one exceptional deal of 18k").

### 2. Newsletter chart from a survey
- **Ask Hermes:** "Chart the 8 answers of our 'biggest blocker' survey question, sorted, highlight the top one."
- **What you get:** a sorted horizontal bar chart with values at the end of each bar, ready to paste in the newsletter.

### 3. Sanity check before an analysis
- **Ask Hermes:** "Plot daily orders from orders.csv before we compute anything."
- **What you get:** a line chart that reveals a gap of five days (export bug), caught before the analysis starts.

## Limits

- Three chart types on purpose. For maps, scatter plots with thousands of points or interactive dashboards, use a BI tool.
- Values are read as numbers with a dot or comma decimal; clean currency symbols first.
- The script draws what you give it: aggregation, outliers and missing periods are your (or the agent's) responsibility.

## Testing

`tests/test_ai_workforce.py` renders the three examples and checks the SVG is well formed and accessible. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`data-forecaster` (plot history plus forecast), `engagement-assessor` (retention and funnels), `anomaly-detector` (mark the anomalies on the line).
