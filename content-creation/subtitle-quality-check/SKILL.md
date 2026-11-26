---
name: subtitle-quality-check
description: Checks an SRT or WebVTT subtitle file for reading speed, line length, overlaps and timing problems, then suggests fixes; use before uploading captions to a video platform.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [subtitles, captions, srt, vtt, video, accessibility]
    category: content-creation
    requires_toolsets: [terminal]
---

# Subtitle Quality Check

Auto-generated captions are often fast, cramped or overlapping. This skill reads a subtitle file, lists every cue that is hard to read, and helps the agent propose concrete fixes (split, merge, retime, reword) without changing the meaning.

## When to use

- You exported captions from a video editor or transcription tool and want a review before upload.
- Viewers say the subtitles flash by too quickly.
- You are about to burn captions into a short vertical video and want them to fit the screen.

## Requirements

- Python 3 (standard library only). No API key, no network.
- A subtitle file in `.srt` or `.vtt` format (UTF-8).

## Usage

1. Run the checker (script path is relative to this skill folder):

```bash
python3 scripts/srt_check.py my-video.srt
```

Optional limits (defaults in brackets): `--max-cps` characters per second [17], `--max-line` characters per line [42], `--max-lines` lines per cue [2], `--min-dur` seconds [1.0], `--max-dur` seconds [7.0]. For narrow vertical video try `--max-line 32`. Add `--json` for machine-readable output. Exit code is 0 when clean, 1 when issues were found, 2 when no cues could be read.

2. Read the report, then open the file and propose fixes for each issue type:
   - `too-fast`: shorten the wording, or extend the end time if the next cue allows it, or split the text across two cues.
   - `too-short`: merge with the neighbouring cue or extend the end time.
   - `too-long`: split at a natural pause.
   - `line-too-long` / `too-many-lines`: break at punctuation or before a conjunction, never in the middle of a name.
   - `overlap` / `out-of-order`: move the later cue's start to the previous cue's end.
   - `double-space`, `empty`, `bad-timing`: clean up directly.
3. Show the user the proposed changes as a before/after list. Write the corrected file under a new name (for example `my-video.fixed.srt`); never overwrite the original.
4. Re-run the checker on the fixed file and report the remaining issues.

Rules for rewording: keep the speaker's meaning and tone, do not add words they did not say, and flag any cue where you were unsure.

## Example output

```
4 cues, 5 issues
  cue 1 (00:01.00) too-fast: 19.0 chars/sec (limit 17)
  cue 2 (00:03.00) too-short: 0.40s on screen (min 1.0)
  cue 3 (00:03.30) too-fast: 45.3 chars/sec (limit 17)
  cue 3 (00:03.30) line-too-long: 77 chars: "This line is intentionally far too long to fit com"
  cue 3 (00:03.30) overlap: starts 0.10s before previous cue ends
```

## Limits

- The thresholds are common rules of thumb, not a platform requirement. Different platforms and audiences may prefer other values; adjust with the options.
- It checks form, not accuracy: misheard words, wrong names and missing punctuation are not detected. The agent should only point out obvious ones it notices while reading.
- Speaker labels, styling tags and positioning cues in VTT are ignored; HTML-like tags are stripped before counting.
- Character counts treat every character the same, so languages written in other scripts may need different limits.

## Testing

```bash
python3 scripts/srt_check.py --selftest
python3 scripts/srt_check.py examples/sample_srt.txt   # exits 1, lists 5 issues
```

Tested on Hermes v0.23.1 on 2026-11-26 (self-test and the sample file both ran as described).
