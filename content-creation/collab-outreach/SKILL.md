---
name: collab-outreach
description: Draft short, personal collaboration messages to other creators from your notes on each profile, then lint the batch for generic flattery, missing offers and copy-paste similarity. Use when you want to reach out to creators or brands without sounding like a template.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [outreach, collaboration, creators, messaging, networking]
    category: content-creation
    requires_toolsets: [terminal]
---

# Collab Outreach

Turn your own notes about other creators into short, honest first messages, then check the whole batch before you send anything. The agent writes only from facts you give it. It never invents shared history, audience numbers or compliments you did not make.

## When to use

- You want to propose a guest appearance, a swap, a joint video, a newsletter mention or a podcast invite.
- You have 3 to 30 people to contact and want each message to feel written for them.
- You want a quick quality check before sending (too long, too generic, no clear ask, no offer).

Not for: mass cold email to people who did not expect it, fake familiarity, or paid promotion that should be disclosed (agree on disclosure first, see your platform's rules).

## Requirements

- Python 3.8+ (standard library only, no API key).
- Your notes, one row per person, with at least: name or handle, platform, what they make, ONE specific piece of their work you really saw, why a collaboration fits, and what you offer.

## Usage

### Step 1: collect notes (agent asks if missing)

For each person, the agent needs these fields. If `specific_detail` or `my_offer` is missing, the agent must ask you instead of guessing:

- `recipient`: name or handle
- `platform`: where you will send it (DM, email, comment)
- `specific_detail`: a real title, topic or moment you saw (e.g. "Cold Brew Ratios video")
- `fit`: one sentence on why the two audiences overlap
- `my_offer`: what they get (a feature, a swap, an intro, a guest spot)
- `ask`: one small, concrete request

### Step 2: draft rules the agent follows

1. Maximum about 100 words. Plain language, no hype.
2. Sentence 1: the specific detail, and what it did for you, in your voice.
3. Sentence 2 to 3: who you are in one line and what you offer.
4. One question only (the ask), small enough to answer in one line.
5. Last line: an easy way out ("no pressure if it's not a fit").
6. No claims about your audience size unless you gave the number and can show it. No "huge fan", no urgency, no promised results.
7. Vary structure between messages. Do not swap only the name.

### Step 3: write the drafts to a CSV and lint them

```
recipient,message,specific_detail
Alice (example),"Hi Alice, your video 'Sourdough for Beginners' fixed my starter problem. ...",Sourdough for Beginners
```

```bash
python3 scripts/outreach_lint.py drafts.csv
python3 scripts/outreach_lint.py drafts.csv --max-words 100 --similarity 0.5
```

Exit code is 0 when everything passes, 1 when something needs fixing, 2 for a bad CSV.

### Step 4: fix and send yourself

The agent rewrites flagged messages and re-runs the lint until clean. You review and send them manually. The skill never sends messages.

## Example output

```
[OK]  Alice (example)
[FIX] Bob (example)
   - specific detail not mentioned in the message
   - generic flattery: 'huge fan'
   - no visible offer: what does the recipient get?
   - no easy way out (e.g. 'no pressure if it's not a fit')

2 messages, 1 need fixes, 0 similar pairs
```

## Limits

- The lint checks wording patterns only. It cannot judge whether your detail is accurate or whether the person wants to hear from you.
- English phrase lists only. Offer and exit-phrase detection is keyword based, so a good message phrased unusually can be flagged (and a poor one can pass).
- The skill does not look up profiles or find contact details. You provide the notes.
- No sending, no scheduling, no follow-up tracking.

## Testing

```bash
python3 scripts/outreach_lint.py --selftest
```

Prints `selftest OK` when the checks behave as expected. Tested on Hermes (local run) on 2026-11-24: the self-test and a two-message demo CSV (one clean, one flagged) both behaved as described above.
