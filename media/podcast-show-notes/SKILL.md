---
name: podcast-show-notes
description: Turn a podcast or video-interview transcript into publish-ready show notes (title options, summary, timestamped key moments, links and resources mentioned); use after recording an episode.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [podcast, show-notes, transcript, srt, vtt, links, content-creation]
    category: media
    requires_toolsets: [terminal]
---

# Podcast Show Notes

Builds the notes that go under an episode: a short description, timestamped key moments, and a verified list of the links and resources mentioned. A small helper script pulls out the facts (links, names of books and tools, candidate moments, speaker labels) with their real timestamps, and the agent writes the text from those facts only.

## When to use

- You finished an episode (audio or video interview) and have a transcript with timestamps.
- You need show notes for a podcast host, a YouTube description or a blog post.
- You want to be sure every link you promised in the episode ends up in the notes.

Not for transcripts without timestamps: ask for an SRT/VTT export, or for lines like `[00:12:30] text`.

## Requirements

- Python 3 (standard library only). No API key, no network.
- A `.srt`, `.vtt` or plain text transcript with timestamps. Speaker labels such as `Alice:` help but are optional.

## Usage

1. Run the helper:

   ```bash
   python3 scripts/notes_prep.py episode.srt
   python3 scripts/notes_prep.py episode.vtt --moments 6
   python3 scripts/notes_prep.py episode.txt --format json
   ```

2. Read its output, then write the notes. Rules for the agent:
   - **Links**: only list a URL that is written in the transcript. For a spoken address ("example dot com slash start"), write it as a proposal and ask the host to confirm the spelling. Never guess a URL for a book or a tool that was only named; write the name and mark it "link to add".
   - **Names**: guest and company names come from the transcript or from the user. If the speaker labels are missing or look like "Speaker 1", ask who is who. Do not add a biography or credentials that nobody said.
   - **Summary**: 3 to 5 sentences, only what was said. No promises like "you will learn everything about...".
   - **Titles**: give 3 options, plain and specific, under about 70 characters, no clickbait that the episode does not deliver.
   - **Key moments**: choose 5 to 8 from the candidates or from the transcript. Keep real timestamps from the file. One line each: `12:30 Why a small list beats a big one`. Do not paraphrase beyond what was said.
   - **Quotes**: copy exactly, with the speaker. Mark cuts with "...".
   - **Sponsors**: if the episode includes a sponsored segment, add a clear line such as "This episode is sponsored by X" (ask the user for the wording they are required to use).

3. Layout to hand back:

   ```
   Title options
   1. ...
   Description
   ...
   Key moments
   0:00 Intro
   ...
   Links and resources
   - Name: https://... (said at 7:00)
   - Name: link to add (said at 9:12)
   To confirm with the host
   - ...
   ```

## Example output

Helper output on a fictional transcript:

```
Duration (last cue): 15:45 | cues: 5
Speaker labels seen: Alice (2), Bob (3)

Links said or written (verify before publishing):
  [9:30] https://example.com/start

Spoken web addresses (heard, spelling to confirm):
  [9:30] example dot com

Resource mentions (book, tool, article...):
  [7:00] Tiny Habits Revisited  <- "Alice: You should check out Simple Writing Tips, and the book called Tiny Habits Revisited."

Key moment candidates:
  [3:10] Bob: The biggest mistake I made was never writing down my own rules for sending.
```

## Limits

- The helper finds resources with simple phrase patterns ("the book called...", "check out..."). It misses many mentions and can pick up wrong words, so the agent must still skim the transcript.
- Key-moment candidates are scored by wording cues, not by understanding. Treat them as a starting point.
- Automatic transcripts contain errors in names and brands: always confirm spellings.
- Only English cue phrases are detected; links and timestamps work in any language.
- The writing steps (titles, summary) are done by the agent and were not benchmarked.

## Testing

```bash
python3 scripts/notes_prep.py --selftest
```

Expected last line: `selftest OK`. It checks SRT parsing, plain-text timestamps, link and spoken-address detection, resource detection and moment selection on a fictional sample.

Tested on Hermes 0.23.1 on 2026-11-23 (helper script self-test and a run on a fictional SRT and a short plain-text file; the agent writing steps were not run end to end).
