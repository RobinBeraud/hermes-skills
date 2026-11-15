---
name: brand-deal-pitch
description: Write a short, honest partnership pitch email to a brand (and a follow-up) from facts the creator provides, with checks against invented figures, hype and missing disclosure; use when a creator or freelancer wants to approach a brand.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [brand-deals, pitch, creators, influencer, outreach, freelance]
    category: content-creation
    requires_toolsets: [terminal]
---

# Brand Deal Pitch

Turn what a creator knows about a brand and about their own audience into a short pitch email that a busy partnerships person can answer in one line. The agent writes the reasoning and the content ideas; the script assembles the email, copies figures and prices exactly as given, and flags hype, stale numbers and missing disclosure. A follow-up email is produced at the same time.

## When to use

- A creator, influencer or marketing/communication freelancer wants to propose a paid or product collaboration to a brand.
- A pitch draft feels long, vague or salesy and needs a structure and a check.
- The creator needs a polite follow-up for a pitch that got no reply.

## Requirements

- Python 3 (standard library only). No API key, no network.
- Script: `scripts/pitch.py` inside this skill folder.

## Usage

### Step 1: Collect facts (the agent never guesses)

Ask the creator, and write down only what they say:
1. Which brand, and who to address (a first name if known, otherwise the team).
2. Why this brand, in 1 to 3 specific reasons: a product they really use, a campaign they can name, a value they share. "I love your brand" is not a reason.
3. Audience figures they want to quote, each with the date read and the source (for example the platform's own analytics). Fewer figures is fine; none is fine.
4. One to three content ideas written for this brand, with the format.
5. Exact deliverables (how many, what format, how many revisions).
6. Their rate, only if they choose to state it. If they do not, leave pricing out and let the email ask for the brand's budget in the call.
7. Timeline, a disclosure line (paid content is labelled as an ad), and one clear ask (usually a short call).

Never invent a rate, a number, a past collaboration or a compliment about the brand.

### Step 2: Write the brief

```bash
python3 scripts/pitch.py --init brief.json
```

This writes an example with fictional data. Replace every value with the creator's facts and delete what they did not provide. Set `pricing.provided_by_creator` to `true` only if the creator gave that exact rate.

### Step 3: Check, then build

```bash
python3 scripts/pitch.py brief.json --check-only
python3 scripts/pitch.py brief.json --out pitch.md
```

- Errors stop the build: no specific reason for the brand, no ideas, no deliverables, no ask, placeholders (TODO, TBD, XXX, ???), a future date, a price not provided by the creator.
- Warnings do not stop it: hype words (for example "guaranteed", "viral"), figures older than 90 days, numbers in the reasons that have no dated proof entry, no disclosure line, more than 3 ideas, a body over 230 words. Read each warning to the creator and decide together.

### Step 4: Personalise by hand, then send

The agent reads the result aloud to the creator. Check that every figure matches the analytics and that each reason is true. Add one sentence in the creator's own voice if the email feels stiff. The creator sends it from their own address. Send the follow-up after the number of days set in the brief only if there was no reply, and send at most one follow-up.

## Example output

```
Subject: Partnership idea for Example Budget App: Budget reset challenge

Hi Sam,

I'm Alex Example, I make plain-language personal finance videos.

Why Example Budget App:
- I have used your envelope-budgeting feature for my own monthly planning since spring.

A few facts about my audience (with date and source):
- 12,400 YouTube subscribers (as of 2026-11-01, YouTube Studio)

What I would make:
- Budget reset challenge (One 8-minute video + 3 short clips): I set up a real monthly budget in your app on camera ...

What you would receive:
- 1 dedicated video, labelled as an ad, one round of revisions
...
Would you be open to a 15-minute call next week to see whether this fits your plans?
```

The file also ends with a short follow-up email. All names, figures and addresses above are fictional.

## Limits

- The script cannot check that figures or reasons are true; the creator is responsible for them.
- It writes one plain-text email in English. Translate or adapt the tone yourself; it does not send anything.
- Number detection is simple: it compares digits in the reasons with the proof and price entries. Counts and durations in ideas, deliverables and timeline are treated as plans, not claims.
- It does not research the brand. The reasons must come from the creator.
- Not legal advice. Rules on advertising disclosure and usage rights vary by country; check the local ones and the contract.

## Testing

```bash
python3 scripts/pitch.py --selftest
```

Expected last line: `ALL PASS`. Tests cover: the example brief, verbatim figures and price, a refused invented price, missing price, future and stale dates, missing reason, placeholders, hype words, unbacked numbers, too many ideas, missing disclosure, and file output.

Tested on Hermes v0.23.1 on 2026-11-15 (selftest and a full build from the example brief).
