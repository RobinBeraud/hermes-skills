---
name: content-repurposer
description: Turns one article, transcribed video or podcast into several formats (LinkedIn post, carousel, thread, newsletter blurb, short-video script) while keeping the author's own voice and facts; use when a creator wants to reuse a piece of content across platforms.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [repurposing, social-media, writing, creators, voice]
    category: content-creation
    requires_toolsets: [terminal]
---

# Content Repurposer

Take one finished piece (article, blog post, video transcript, podcast transcript) and produce several platform-ready drafts that still sound like the author and never change a fact. A small helper script builds a "source brief" first (voice fingerprint, quotable lines, numbers and links to preserve) so the drafts are grounded in the source instead of in generic marketing tone.

## When to use

- "Turn this article into a LinkedIn post, a thread and a newsletter blurb."
- "Here is my video transcript, give me a carousel and a short script."
- You want one idea to travel across platforms without rewriting from scratch.

Not for: inventing new content, translating, or adding claims the source does not make.

## Requirements

- Python 3.8+ (standard library only, no network, no API key).
- A text file: `.md`, `.txt`, `.srt` or `.vtt` (timestamps are stripped automatically).

## Usage

1. Build the brief:

```bash
python3 scripts/source_brief.py my-article.md            # readable Markdown
python3 scripts/source_brief.py my-video.srt --json      # same, as JSON
```

2. Read the brief, then read the source once more. Decide the single core idea (one sentence). Every output must serve that idea.

3. Draft each requested format following these rules:
   - **Voice**: match the fingerprint. If sentences are short and the author says "you" and "I", write that way. Do not add emojis, hashtags or exclamation marks the author does not normally use.
   - **Facts**: use only numbers, names and claims in `facts_to_preserve` or the source text. If a format needs a number the source lacks, leave a placeholder like `[ADD YOUR NUMBER]`, never invent one.
   - **Quotes**: reuse lines from `quotable_lines` verbatim; mark any paraphrase as paraphrase.
   - **Links**: only links present in the source, or ones the user gives you.
   - **Sponsorship**: if the source is sponsored or contains affiliate links, keep the disclosure in every derived format.
   - **No clickbait that the content cannot pay off**: the hook must be answered by the piece.

4. Format guide (targets, adjust to the author's habits):
   - **LinkedIn post**: a one-line hook, short paragraphs, one concrete example from the source, one closing question or call to action. Keep it shorter than the source's summary.
   - **Thread**: one idea per post, numbered, first post is the hook, last post points back to the original.
   - **Carousel**: 6 to 9 slides, one sentence per slide plus a title; slide 1 = promise, last slide = call to action. Output as a list "Slide N: title / text".
   - **Newsletter blurb**: 3 to 5 sentences plus a "read the full piece" line.
   - **Short-video script**: hook in the first spoken sentence, 3 beats, a payoff, on-screen caption suggestions. Aim for under 60 seconds of speech (about 130 words).
   Platform limits change over time: tell the user to check the current character limits before posting.

5. End with a short "Fact check" list: for every number or quote used, say where in the source it appears. Remind the user the drafts must be reviewed before publishing.

## Example output

Brief excerpt (from a made-up article about batch filming):

```
## Voice fingerprint
- avg_sentence_words: 8.7
- reads as: short punchy sentences; speaks to the reader directly ('you'); personal ('I', 'we'); casual (contractions)
## Quotable lines (verbatim, reuse as-is)
- Stop filming when the spark is gone.
## Facts to preserve exactly
- 3 hours
```

Resulting LinkedIn draft opening:

```
I used to film ten videos in one Saturday.
By video four, you could see my energy was gone.
Stop filming when the spark is gone.
...
Fact check: "3 hours" and "6 hours" come from paragraph 2 of the source.
```

## Limits

- The voice fingerprint is a rough statistical hint (sentence length, pronouns, contractions, emoji). It does not capture humor or style fully; the agent must still read the source.
- "Key sentences" and "quotable lines" are picked by simple word-frequency and length rules, so review them; they are suggestions, not truth.
- English-oriented heuristics (pronoun and stop-word lists). Other languages still get sentence, number and link extraction, but the voice labels are less reliable.
- The script does not post anywhere, fetch URLs or call any platform API.
- Platform length limits are not encoded on purpose, because they change.

## Testing

```bash
python3 scripts/source_brief.py --selftest   # prints: selftest OK
python3 scripts/source_brief.py scripts/../SKILL.md | head
```

Tested on Hermes (cron agent session) on 2026-11-10: selftest passed and the brief was generated for a short fictional article. The drafting step (instructions only) was not run against a real long transcript. Status: script tested, drafting workflow untested at scale.
