---
name: trend-watcher
description: Identify emerging and fading topics in large streams of dated text (support tickets, reviews, survey answers, social posts, news titles) by comparing a recent window with a baseline, with a dependency-free Python script. Use for a weekly "what is new, what is growing, what is going away" brief backed by counts.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [trends, text-mining, voice-of-customer, market-watch, support, weak-signals, ai-workforce]
    category: ai-workforce
    requires_toolsets: [terminal]
    related_skills: [research-assistant, anomaly-detector, data-forecaster, content-creator]
---

# Trend Watcher

The Trend Watcher spots emerging patterns before they are obvious. It counts in how many items each word and two-word phrase appears in the last weeks versus the weeks before, ranks the biggest risers and fallers, and merges terms that always appear together (they are one signal). The agent then reads a sample of the matching items and turns the numbers into a short brief.

## When to use

- Support wants to know which problems are new this fortnight.
- Product reviews or survey answers pile up and nobody reads them all.
- A market or competitor watch should surface what is gaining attention, from RSS titles or social posts.

## How the agent works

1. **Collect** items with a date and a text: CSV (`date,text`) or JSON Lines. Ticket subjects, review texts, post bodies, article titles.
2. **Set windows:** recent (default 14 days) and baseline (default 56 days just before). The recent window ends at the latest item or at `--end`.
3. **Run the script.** Emerging terms need at least `--min-count` recent items and a lift of 1.5 or more; fading terms need a solid baseline.
4. **Read before concluding.** For the top 5 emerging terms, the agent reads 3 matching items each and names the underlying topic ("2FA codes by SMS not received since the update").
5. **Brief:** topic, size (share of items now vs before), first seen, example quote (anonymised), suggested owner. Weekly, as a cron job.

## Usage

```bash
python3 scripts/trends.py examples/support_tickets.csv --date-col date --text-col text --recent-days 14 --baseline-days 56
python3 scripts/trends.py posts.jsonl --jsonl --date-col published --text-col title --top 10 --json
```

Example output on the bundled support tickets:

```
Recent 2026-10-27 to 2026-11-09 (66 items) vs baseline 2026-09-01 to 2026-10-26 (253 items)

Emerging:
  code                           0.0% ->  21.2% of items  (x109.94, 14 recent)  + sms
  bank sync                      0.0% ->  19.7% of items  (x102.36, 13 recent)  + bank, sync
  two-factor                     0.0% ->  18.2% of items  (x94.78, 12 recent)

Fading:
  invoice pdf                   14.2% ->   4.5% of items  (x0.36, 3 recent)  + shows wrong, pdf shows, wrong vat
```

## Documented use cases

### 1. Weekly support brief
- **Ask Hermes:** "trend-watcher: every Monday, run on last 70 days of tickets and send the product team the 3 emerging issues with an example each."
- **What you get:** "New: SMS 2FA codes not received (21% of tickets this fortnight, 0% before), started after the 4 November update. Fading: wrong VAT on invoice PDF, fixed in release 3.2."

### 2. Review mining after a launch
- **Ask Hermes:** "Compare app store reviews of the 2 weeks after the redesign with the 8 weeks before."
- **What you get:** rising themes (navigation, dark mode), fading themes (slow loading), each with counts and two quotes.

### 3. Market watch from RSS titles
- **Ask Hermes:** "Collect the titles of these 12 industry feeds daily and tell me on Friday which topics are rising."
- **What you get:** a list of rising phrases with links to the articles behind them, ready for `content-creator` to turn into a newsletter section.

## Limits

- Counting words, not understanding them: synonyms ("refund", "money back") are separate terms. The reading step covers that.
- English and French stop words are built in; other languages work but with more noise.
- Small volumes (under 50 recent items) give unstable lifts. Widen the window.
- Texts may contain personal data: anonymise quotes before sharing them.

## Testing

`tests/test_ai_workforce.py` plants a new topic in recent tickets and checks it ranks first and that a fixed bug shows as fading. Tested locally with Python 3.12 on 2026-11-10.

## Works well with

`research-assistant` (explain why a topic rises), `anomaly-detector` (volume spikes), `content-creator` (turn the brief into a post), `content-guardian` (anonymise quotes).
