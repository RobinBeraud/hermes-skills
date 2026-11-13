---
name: content-calendar-30-days
description: Build a 30-day editorial calendar from 3 content pillars, with topics, formats, platforms and recycling of past top posts; use when a creator or freelancer needs a posting plan for the next month.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [content-calendar, editorial-planning, social-media, creators, planning]
    category: content-creation
    requires_toolsets: [terminal]
---

# Content Calendar (30 days)

Turn three content pillars into a month of posts: one row per post with date, platform, pillar, format, topic, and a clear slot for recycling your best older content. A small script builds the skeleton (dates, rotation, balance); the agent fills in the topics with the creator.

## When to use

- A creator, influencer, or marketing/communication freelancer asks for "a content plan for next month".
- Someone posts irregularly and wants a realistic rhythm.
- A client needs a calendar to approve before production.

## Requirements

- Python 3 (standard library only). No API key, no network.
- Script: `scripts/calendar_plan.py` inside this skill folder.

## Usage

### Step 1: Ask the creator (keep it short)

Collect, and do not guess if missing:
1. Three pillars (recurring themes), e.g. Teach / Behind the scenes / Proof. If they have none, propose three based on their niche and let them edit.
2. Platforms they actually use (1 to 3 is realistic).
3. Posts per week they can really sustain. Suggest fewer rather than more.
4. Start date.
5. Their best past posts (titles or links), if any, for the recycling slots.
6. Anything fixed: launches, holidays, events, sponsored content already agreed.

### Step 2: Generate the skeleton

```bash
python3 scripts/calendar_plan.py \
  --pillars "Teach,Story,Proof" \
  --platforms "instagram,linkedin" \
  --start 2026-12-01 --per-week 3 --recycle-every 5 \
  --out calendar.csv
```

Use `--format md` for a table to paste in a document. The balance summary goes to stderr; read it. Platforms with built-in format lists: instagram, tiktok, linkedin, youtube, x, newsletter, blog. Other names get generic formats.

### Step 3: Fill the topics (the agent's real job)

For each row, replace `TODO`:
- One specific topic, written as a promise to the audience, not a vague theme ("3 mistakes when pricing a first freelance project", not "pricing tips").
- Respect the pillar and the suggested format. Change the format only if it does not fit, and say so.
- Recycling rows: pick one of the creator's real past posts for `recycle_from`, and give a new angle or a new format (a carousel becomes a short video, a thread becomes a newsletter). Never invent past posts. If the creator gave none, leave the slot for them and say so.
- Place fixed events from Step 1 first, then fill around them.
- Any sponsored or paid content must be marked as such in the topic and disclosed in the final post.

### Step 4: Check and hand over

```bash
python3 scripts/calendar_plan.py --check calendar.csv
```

It flags empty topics, duplicate topics, recycling slots without a source and the same pillar twice in a row. Fix what it reports, then give the creator the file plus a three-line summary: posts count, pillar split, what still needs their input.

## Example output

```
| Date | Day | Platform | Pillar | Format | Topic | Recycle from |
| 2026-12-02 | Wed | instagram | Teach | carousel | TODO | |
| 2026-12-05 | Sat | linkedin | Story | text post | TODO | |
| 2026-12-12 | Sat | instagram | Story | single image | TODO: new angle on the recycled post | TODO: best past post on this pillar |
```

After Step 3 the `TODO` cells hold real topics, and `--check` reports `0 problems` style output (no `PROBLEM:` lines, exit code 0).

## Limits

- The script does not choose topics, judge quality or know your audience; the agent and the creator do that.
- It does not suggest best posting times; it has no audience data. Do not claim any.
- It spreads posts evenly across weekdays; it ignores holidays and time zones.
- Format lists are generic defaults, not platform rules.
- The recycling slots are placeholders until the creator provides real past posts.
- Status: the script is tested with its self-test and sample runs. The topic-writing workflow is instructions only and has not been evaluated on real creator accounts.

## Testing

```bash
python3 scripts/calendar_plan.py --selftest
```

Expected: `selftest OK: 13 posts`. Also run a generation, then `--check` on the untouched file: it must exit with code 1 and list empty topics.

Tested on Hermes v0.23.1 on 2026-11-13: self-test and sample generation, balance warnings and `--check` executed successfully.
