---
name: youtube-title-thumbnail-brief
description: Turn a video idea into several matching title + thumbnail pairs with a short designer brief, then check length, readability and honest wording before you publish.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [youtube, title, thumbnail, creators, content]
    category: content-creation
    requires_toolsets: [terminal]
---

# YouTube Title and Thumbnail Brief

A title and a thumbnail are read together, in about a second, in a list of other videos. This skill helps the agent propose several pairs that work as one message, write a brief someone else could turn into a thumbnail, and run a small checker that flags titles that are too long, thumbnails with too much text, and wording that promises more than the video delivers.

## When to use

- You have a video idea or a finished script and need title and thumbnail options.
- Your thumbnail text just repeats the title.
- You work with a designer or editor and want a clear thumbnail brief instead of "make it pop".
- You want a last honesty check before publishing.

## Requirements

- Python 3 (standard library only) for the checker. No API key, no network.
- From the user: the video topic, what the viewer will concretely get or learn, the target viewer, and any real result shown in the video (only real ones).

## Usage

1. Ask only for what is missing: topic, the one concrete outcome of the video, who it is for, and what is truly shown on screen.
2. Propose 5 pairs. Each pair has:
   - a title that names the subject and hints at the outcome,
   - thumbnail text of at most 4 words that adds something the title does not say (a question, a contrast, a result, a number the video really contains),
   - a visual description in one sentence: who or what is shown, the expression or action, the background, the main colour contrast.
3. Vary the angle across the pairs: how-to, a test or comparison, a mistake to avoid, a before/after, a question. Do not write five rewordings of the same title.
4. Write the pairs to a text file, one per line, in this format:

```
title | thumbnail text | visual description
```

5. Run the checker:

```bash
python3 scripts/pair_check.py /tmp/candidates.txt
```

   Options: `--max-title 60` (character limit, default 60) and `--max-thumb-words 4`. Raise or lower them to match your channel and habits; they are guidelines, not platform rules.
6. Fix every `[BLOCK]` and `[FIX]` line, consider each `[WARN]`, and run again until it prints `OK`.
7. Recommend one pair and say why in two sentences. Suggest running the two best pairs as an A/B test if the user's tools allow it, without claiming which will win.
8. For the chosen pair, write the designer brief: the three elements to keep (one face or object, one short text, one contrasting colour), what to leave out, and the exact thumbnail text.

Rules for the agent: never promise results the video does not show, never invent numbers, never use someone else's face or brand without permission, keep wording plain.

## Example output

Input file (fictional channel):

```
I tested 5 free editing apps on a phone | Which is best? | Creator holding a phone, curious face, five app icons behind
SHOCKING: you won't believe this editing trick!! | WOW | face
How to edit a video on your phone | Edit a video on phone | Phone screen close-up
```

Checker output:

```
[WARN] line 2: too many exclamation marks
[BLOCK] line 2: promise-style wording 'you won't believe'; only promise what the video really shows
[BLOCK] line 2: promise-style wording 'shocking'; only promise what the video really shows
[FIX] line 2: visual description is too short to brief a designer (who or what is shown, where, which expression)
[FIX] line 3: thumbnail text has 5 words (limit 4); it must be readable at small size
[FIX] line 3: thumbnail text only repeats the title; add a new angle (a result, a question, a contrast)
```

Exit code is 1 when any `[BLOCK]` or `[FIX]` is printed, otherwise 0. Line numbers are file line numbers.

## Limits

- The checker looks at character counts, word counts, a short list of English exaggeration phrases and word overlap. It cannot judge whether a title is interesting or whether a thumbnail looks good.
- The default limits (60 characters, 4 words) are rules of thumb, not official figures. Display length varies by device and screen.
- It does not generate images and does not know how your audience reacts. Use your own analytics to compare results.
- English wording only.

## Testing

```bash
python3 scripts/pair_check.py --selftest
```

Prints the sample problems and `SELFTEST OK`. Tested on Hermes v0.23.1 on 2026-11-22 (selftest plus two sample files: one clean, one with an overlong title).
