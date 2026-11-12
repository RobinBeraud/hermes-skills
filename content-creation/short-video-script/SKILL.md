---
name: short-video-script
description: Write a short-form video script (Reel, TikTok, YouTube Short) with a hook, tension, payoff, call to action, shot notes and caption chunks, then check its timing. Use when a creator needs a ready-to-film script from a topic or rough idea.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [video, shorts, reels, tiktok, scripting, creator]
    category: content-creation
    requires_toolsets: [terminal]
---

# Short Video Script

Turns a topic or a rough idea into a script for a vertical video of about 15 to 45 seconds. Each line has the words to say and a visual note. A small helper script estimates how long it takes to speak and splits the words into caption chunks.

## When to use

- The user has a topic, a tip, a story or a product and wants a script for a Short, Reel or TikTok.
- The user already has a draft and wants to know if it is too long or if the opening is too slow.
- The user needs subtitle text split into short readable pieces.

## Requirements

- Python 3 (standard library only). No API key, no network.
- Information from the user: topic, target platform, who the viewer is, desired length (default 30 seconds), and the one action the viewer should take at the end. If something is missing, make a reasonable assumption and state it in one line. Do not interrogate the user.

## Usage

### 1. Gather the brief (in your head, then state it in 3 lines)

- Viewer: who watches and what they want.
- Promise: the one thing the video delivers.
- Action: the one next step (follow, comment, click the link in bio, try something).

### 2. Write the script in this exact line format

Each line starts with a label. Visual notes go in [square brackets] and are not spoken.

```
HOOK: <the opening sentence, spoken in about 3 seconds> [visual]
BEAT: <setup or step> [visual]
BEAT: <step> [visual]
TURN: <the surprise, the proof or the payoff> [visual]
CTA: <one clear next step> [visual]
```

Rules for writing:
- HOOK: one sentence, around 8 words or fewer. Start with the result, a question the viewer cares about, or a contradiction. No greeting, no "hey guys", no introduction of yourself.
- BEAT: one idea per line, short spoken sentences, concrete words. Two to four beats.
- TURN: the moment the promise is kept. Do not hide it until the last second.
- CTA: exactly one action. Not "like, follow, comment and share".
- Every line needs a visual note that changes something on screen (a new angle, text overlay, screen recording, object). A talking head with no change for 10 seconds loses attention.
- Only state facts the user gave you. Do not invent numbers, results, testimonials or sources. If the video would be stronger with a figure, write a placeholder like `[YOUR NUMBER]` and tell the user.
- If the video promotes a brand or a paid partnership, add a visible disclosure note in the first visual (for example text on screen saying "Ad" or "Paid partnership") and mention it to the user. Follow the platform's own rules for labelling.

### 3. Save it and check the timing

Save the script to a text file (for example `/tmp/my_short.txt`), then run:

```bash
python3 scripts/script_timer.py /tmp/my_short.txt --target 30 --hook-max 3
```

Options: `--wps` (speaking pace in words per second, default 2.5), `--target` (max seconds, default 45), `--hook-max` (max seconds for the hook, default 3), `--chunk` (words per caption chunk, default 4). Use `-` as the file name to read from standard input.

Exit code 0 means no problem, 1 means the check found problems, 2 means the file could not be read.

### 4. Fix what the check reports, then deliver

Rewrite lines that are flagged (hook too long, total too long, missing CTA, missing visual). Re-run until clean. Deliver to the user: the final script, the estimated duration, and the caption chunks. Offer two alternative hooks only if the user asks.

## Example output

Input file:

```
HOOK: You are editing your videos in the wrong order. [close-up, text on screen: WRONG ORDER]
BEAT: Most people cut the footage first and add sound last. [screen recording of a timeline]
BEAT: Start with the voice track, then cut the picture to match it. [split screen]
TURN: The video suddenly feels faster without any new effects. [before/after]
CTA: Try it on your next clip and tell me what changed. [face to camera]
```

Command `python3 scripts/script_timer.py my_short.txt --hook-max 4` prints:

```
Estimated speaking pace: 2.50 words/second
00:00.00-00:03.60  HOOK   9 words  3.6s
00:03.60-00:07.60  BEAT  10 words  4.0s
00:07.60-00:12.40  BEAT  12 words  4.8s
00:12.40-00:16.00  TURN   9 words  3.6s
00:16.00-00:20.40  CTA   11 words  4.4s
TOTAL: 20.4s (target 45s)

Caption chunks:
1
00:00.000 --> 00:01.600
You are editing your
...
No problems found.
```

With the default `--hook-max 3` the same file reports: `hook takes about 3.6s to say, limit is 3.0s (9 words)`.

## Limits

- Timing is an estimate from word count and a fixed pace. Real speech varies, so record a take and adjust `--wps` (try 2.2 for calm delivery, 3.0 for fast).
- The checker does not judge whether the hook is good, only its length, and it cannot see the video. Hook quality is the agent's job: follow the writing rules above.
- Caption chunks are plain text with estimated times, not a final subtitle file. Import and retime them in your editor.
- The checker works with spoken words only. Numbers written as digits count as one word each.
- The skill does not predict views or performance and must never claim to.

## Testing

```bash
python3 scripts/script_timer.py --selftest
python3 scripts/script_timer.py /tmp/my_short.txt
```

The selftest checks parsing, timing, and detection of a missing hook, missing CTA, overlong hook and overlong total. Status: tested. Tested on Hermes v0.23.1 on 2026-11-12 (selftest passes; the example above was run and its output copied).
