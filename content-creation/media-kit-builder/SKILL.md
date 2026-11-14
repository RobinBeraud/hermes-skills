---
name: media-kit-builder
description: Build a clean, printable one-page HTML media kit from the figures a creator provides, refusing to invent statistics; use when a creator or freelancer needs a media kit to send to brands.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [media-kit, creators, brand-deals, influencer, freelance]
    category: content-creation
    requires_toolsets: [terminal]
---

# Media Kit Builder

Turn the facts a creator gives you (audience figures, best content, services, contact) into a tidy one-page media kit that opens in any browser and prints to PDF. The script copies figures exactly as given, requires a date for each one, and leaves out any section that has no data. It never fills gaps with made-up numbers.

## When to use

- A creator, influencer, or marketing/communication freelancer needs a media kit for brand outreach.
- An existing kit is out of date and needs a refresh with current figures.
- A client wants a presentable one-pager but has only screenshots or numbers in a message.

## Requirements

- Python 3 (standard library only). No API key, no network.
- Script: `scripts/media_kit.py` inside this skill folder.

## Usage

### Step 1: Collect real facts (the agent never guesses)

Ask for, and write down only what the creator actually states:
1. Name, one-line tagline, short bio (2 to 3 sentences, in the creator's own words if possible).
2. For each platform: handle and the audience figure as shown in the platform's own analytics, plus the date the figure was read and where it came from (for example "YouTube Studio").
3. Audience details (top countries, age ranges) only if they have them, each with a date and source.
4. One to three best-performing pieces of content, with the metric and date.
5. Past collaborations they are happy to name. Check that each one was real and that they can mention it.
6. Services and prices. If they prefer not to publish prices, write "On request" themselves.
7. Contact details and a one-line disclosure policy (for example, that paid content is always labelled).

If a figure is missing, leave it out. Do not round up, estimate, or "ballpark". If they only have a screenshot, read the numbers from it and confirm them back.

### Step 2: Write the input file

```bash
python3 scripts/media_kit.py --init kit.json
```

This writes an example with fictional data. Replace every value with the creator's real facts; delete entries they did not provide. Each figure needs `as_of` (YYYY-MM-DD) and should have `source`.

### Step 3: Check, then build

```bash
python3 scripts/media_kit.py kit.json --check-only
python3 scripts/media_kit.py kit.json --out media-kit.html
```

- Errors stop the build: missing or invalid date, future date, leftover placeholders (TODO, TBD, XXX, ???).
- Warnings do not stop it: figures older than 90 days, missing source, no contact, no disclosure line. Read each warning to the creator and decide together.

### Step 4: Review and export

Open `media-kit.html` in a browser and use Print, then Save as PDF. Read it through with the creator: every number on the page must match what they gave you. Remind them to refresh the figures before each outreach campaign.

## Example output

```
WARN: platforms[1]: figure is 112 days old, refresh before sending
wrote media-kit.html (1 warning(s))
```

The HTML contains: name and tagline, "Where to find me" cards (each figure labelled "as of <date>, source: <name>"), Audience, Best content, Past collaborations, Services, and a footer with the disclosure line and contact details. Sections without data do not appear.

## Limits

- Design is one simple layout (A4-friendly, black and white). No logos, photos, or colour themes.
- The script cannot verify that figures are true. It only enforces that they are dated and copied verbatim. The creator is responsible for their accuracy.
- Staleness is judged by the `as_of` date against today's date on the machine.
- PDF export is done by the browser's Print dialog, not by the script.
- Not legal advice. Rules on advertising disclosure vary by country; check the local ones.

## Testing

```bash
python3 scripts/media_kit.py --selftest
```

Expected last line: `ALL PASS`. Tests cover: valid example, missing date, placeholder text, stale and future dates, HTML escaping, verbatim figures, omitted empty sections, and file output.

Tested on Hermes v0.23.1 on 2026-11-14 (selftest and a full build from the example file).
