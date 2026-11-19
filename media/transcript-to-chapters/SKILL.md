---
name: transcript-to-chapters
description: Turn a timestamped transcript (SRT or VTT) into YouTube chapters, a short summary and quote candidates for social posts; use after recording a video or podcast when you need chapters and post material.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [youtube, chapters, transcript, srt, vtt, video, podcast, repurposing]
    category: media
    requires_toolsets: [terminal]
---

# Transcript to Chapters

Reads a subtitle file (SRT or VTT), finds where the topic changes, and helps the agent produce: a chapter list ready to paste in a video description, a short summary, and a few quotes to reuse in posts.

## When to use

- You have a subtitle or transcript export with timestamps and want chapters for the video description.
- You want 3 to 8 quotable lines with their timestamps for posts or a newsletter.
- You want a quick summary of a long recording without rewatching it.

Not for transcripts without timestamps (no times means no chapters; ask for an SRT/VTT export instead).

## Requirements

- Python 3 (standard library only). No API key, no network.
- A `.srt` or `.vtt` file. Most video platforms and editing tools can export one.

## Usage

1. Run the helper on the file. It prints chapter candidates (start time, dominant keywords, opening words) and quote candidates:

   ```bash
   python3 scripts/chapters.py episode.srt
   python3 scripts/chapters.py episode.vtt --chapters 6 --min-seconds 90
   python3 scripts/chapters.py episode.srt --format json
   ```

2. The script only finds *where* topics shift. The agent writes the content:
   - **Titles**: 2 to 6 words, say what the viewer will learn or see, no clickbait, no all-caps. Base each title on that chapter's keywords AND its opening words; if unsure, read that part of the transcript.
   - **Merge or move boundaries** when the script cut mid-explanation. Moving a start time to the beginning of the sentence that introduces the new topic is allowed; keep it a real timestamp from the file.
   - **Summary**: 2 to 4 sentences using only what is said in the transcript.
   - **Quotes**: pick 3 to 5 from the candidates (or from the transcript), copy the wording exactly, keep the timestamp, and never change meaning. If you shorten a quote, mark the cut with "...". Do not attribute a quote to anyone other than the speaker(s) in the file; ask who is speaking if several people are.
3. Check YouTube's rules (the script prints a check): first chapter at `0:00`, at least 3 chapters, each at least 10 seconds long. Format in the description is one line per chapter: `0:00 Title`.

Answer layout to give the user:

```
Chapters (paste in the description)
0:00 Intro
...

Summary
...

Quotes
[2:10] "..."
```

## Example output

Running on a small built-in sample (a 5 minute bread-baking talk):

```
Transcript length: 5:30  |  cues: 8

## Chapter candidates (titles to be written by the agent)
- 0:00  keywords: starter, flour, dough, bread, water, welcome
- 2:10  keywords: dough, fold, every, thirty, minutes, four
- 3:00  keywords: oven, baking, time, preheat, heavy, pot
## YouTube rules check: OK
```

The agent then turns this into, for example, `0:00 Starter and flour basics`, `2:10 Folding the dough`, `3:00 Preheating and baking`.

## Limits

- Boundaries come from word overlap between neighbouring 30-second blocks. They are suggestions: on short or very uniform talks they can miss a real topic change or cut in the wrong place. The agent must review them.
- Keywords are plain word counts; they do not understand meaning. Titles need human-style reading of the text.
- Quote candidates are sentences of 8 to 28 words picked by a simple heuristic, not by how good they sound.
- Auto-generated captions contain errors; check quote wording against the video before publishing.
- Tested only on a small synthetic English sample and a minimal VTT snippet. Other languages work for parsing, but the stop-word list is only English and French. Real-world long recordings: Status: untested.

## Testing

```bash
python3 scripts/chapters.py --selftest
```

Expected: `selftest OK: [...]`. The self-test parses SRT and VTT, builds chapters, checks the YouTube rules and extracts quotes.

Tested on Hermes v0.23.1 on 2026-11-19 (selftest and a run on the built-in sample).
