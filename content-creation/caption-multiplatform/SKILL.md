---
name: caption-multiplatform
description: Adapts one caption idea into separate versions for Instagram, TikTok, LinkedIn and YouTube (length, tone, hashtags, call to action) and checks each version with a small local script. Use when you have one message to publish on several platforms.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [captions, social-media, copywriting, instagram, tiktok, linkedin, youtube]
    category: content-creation
    requires_toolsets: [terminal]
---

# Caption Multiplatform

Turn one message into platform-specific captions instead of pasting the same text everywhere. The agent writes the versions; a small script checks length, hashtags, first-line length, call to action and sponsorship disclosure.

## When to use
- You have one post, video or announcement and want it on several platforms.
- You want each caption to read as native to its platform, not copy-pasted.
- The post is sponsored or gifted and you want a reminder that disclosure wording is present.

## Requirements
- Python 3 (standard library only). No API key, no network.
- Platform limits change. The defaults in the script are starting values: check each platform's current help page and override them with `--limits my_limits.json` (see `--dump-limits`).

## Usage

### 1. Gather the brief
Ask the user, in plain words, for:
1. The core message in one or two sentences.
2. The audience and the voice they normally use (ask for one or two past captions if they have them; copy the style, not the text).
3. The single action they want people to take (comment, save, read, click a link).
4. Target platforms (default: Instagram, TikTok, LinkedIn, YouTube).
5. Whether the post is sponsored, gifted, or contains affiliate links.

### 2. Write one version per platform
Keep the same core message and change the shape:
- **Instagram**: hook in the first line (it is what shows before "more"), short paragraphs, a small set of relevant hashtags at the end, one clear action.
- **TikTok**: very short, conversational, the caption supports the video rather than repeating it; a question works well as the action.
- **LinkedIn**: professional but human, first-person, one lesson or observation, line breaks for readability, few or no hashtags.
- **YouTube**: a description that starts with the key sentence, then context, links and optional chapters; the title is handled separately.
Rules: no invented numbers or results, no false urgency, no engagement bait such as "comment YES to win" unless a real giveaway exists. Do not use long dashes.
If the post is sponsored, include clear wording such as `#ad` or "Paid partnership with ..." near the start, and follow the platform's own disclosure tool in addition.

### 3. Save and check
Save the versions in a file with one `## platform` heading per caption, then run:

```bash
python3 scripts/caption_check.py captions.md
python3 scripts/caption_check.py captions.md --sponsored
python3 scripts/caption_check.py captions.md --limits my_limits.json
python3 scripts/caption_check.py --dump-limits > my_limits.json
```

Exit code 0 means no warnings, 1 means at least one warning. Fix each warning and re-run. The checks are heuristics: a warning such as "no call to action found" is a prompt to look, not a verdict.

### 4. Deliver
Give the user the final captions, one block per platform, plus a short list of what you changed between platforms and why.

## Example output
```
[instagram] 172 chars, 2 hashtags, first line 99 chars
  OK
[tiktok] 85 chars, 0 hashtags, first line 40 chars
  - first line is mostly capitals
[linkedin] 114 chars, 0 hashtags, first line 62 chars
  - no call to action found
```

## Limits
- The script never reads platform pages: limits are editable defaults and may be outdated. Verify them.
- Call-to-action and disclosure detection use simple word matching and can miss or over-detect. Disclosure rules differ by country: this skill does not give legal advice.
- Writing quality depends on the brief and on any voice samples supplied.
- It does not post anything for you.

## Testing
```bash
python3 scripts/caption_check.py --selftest
```
Expected: `selftest OK`. A sample file with three captions was also run and produced the output shown above.
Status: script tested locally, writing instructions not evaluated across many real briefs.
Tested on Hermes (cron agent) on 2026-11-20.
