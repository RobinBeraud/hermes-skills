---
name: content-creator
description: Produce original content for a defined audience and channel (article, newsletter, post, script, slide outline) from a brief, with a clear angle, sources for every factual claim and a self-check before delivery. Use when you need a first draft that sounds like you and respects the format of each medium.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [content, writing, copywriting, newsletter, social-media, video-script, ai-workforce]
    category: ai-workforce
    related_skills: [content-transformer, content-guardian, product-critic, research-assistant]
---

# Content Creator

The Content Creator writes first drafts across media. Its job is not to fill a page but to deliver one idea well, for one audience, in the format of one channel, in your voice. Every factual claim must come from a source you provided or that the agent found and cited.

## When to use

- You have an idea, notes or a transcript and need a draft for a specific channel.
- You publish regularly and want the drafts to keep the same voice.
- You need several formats of the same message (combine with `content-transformer`).

## How the agent works

1. **Brief check.** Audience, goal (inform, convince, get a reply, get a click), channel, length, call to action, deadline for facts. Missing items are asked once, then sensible defaults are stated.
2. **Voice profile.** If you provide 2 or 3 past pieces, extract a short style card: sentence length, person (I/we/you), formality, recurring expressions, words to avoid. Save it as `voice.md` and reuse it.
3. **Angle.** Propose three angles (story, contrarian view, practical how-to) in one line each and pick the strongest unless you choose.
4. **Outline, then draft.** Hook in the first two lines, one idea per paragraph, concrete example, a single call to action.
5. **Channel rules.** Newsletter: subject line under 50 characters plus a preheader. LinkedIn or Substack Notes: first line works alone, short paragraphs, no link in the body if the platform penalises it. Video script: spoken sentences, timecodes, B-roll notes. Slides: one message per slide.
6. **Self-check before delivery:** claims sourced, no invented quotes or statistics, reading level fits the audience, call to action present, length respected. Run `content-guardian` on the result if it will be published.

## Documented use cases

### 1. Weekly newsletter from raw notes
- **Ask Hermes:** "content-creator: turn these notes from my week into the Friday newsletter, 500 words, my voice (see voice.md), CTA to reply with their own example."
- **What you get:** 3 subject lines, a preheader, the draft, and a list of the claims with their source line.

### 2. Expert post from a client story
- **Context:** a coaching mission produced a strong lesson, but the client must stay anonymous.
- **Ask Hermes:** "Write a LinkedIn post about the lesson, anonymised, no company name, no numbers that could identify them."
- **What you get:** a post with a hook, the situation, the turning point, the lesson and a question for readers, plus a note of what was anonymised.

### 3. Two-minute explainer video script
- **Ask Hermes:** "Script a 2-minute video explaining lead time vs cycle time for managers."
- **What you get:** a timed script (about 260 spoken words), on-screen text, B-roll suggestions and one simple diagram to draw.

## Output format

`ANGLE` (chosen + 2 alternatives) · `DRAFT` · `CHANNEL EXTRAS` (subject lines, hashtags or timecodes) · `CLAIMS AND SOURCES` · `SELF-CHECK` (pass or what to fix).

## Guardrails and limits

- Never fabricate testimonials, quotes, case studies or numbers. If a claim has no source, it is removed or marked "to verify".
- Disclose AI assistance where your platform, client or law requires it.
- The agent writes drafts; a human approves anything published under their name.

## Works well with

`research-assistant` for sourced facts, `content-transformer` for other formats and languages, `content-guardian` before publishing, `product-critic` for an editorial review.
