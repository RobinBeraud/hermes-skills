---
name: content-transformer
description: Adapt existing content between formats, audiences and languages (article to thread, webinar to blog post, report to one-pager, English to French) while keeping the meaning, facts and voice, with a fidelity check that lists what was cut or changed. Use when one good piece should work in several places.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [repurposing, translation, localization, summarization, content-ops, ai-workforce]
    category: ai-workforce
    related_skills: [content-creator, content-guardian, research-assistant]
---

# Content Transformer

The Content Transformer adapts existing content between formats and languages. It is the opposite of starting from a blank page: the source is the truth, and the job is to fit it to a new medium, length or culture without inventing anything. Every transformation ends with a fidelity check, so you know what was dropped, merged or reworded.

## When to use

- A webinar, podcast or talk should also become an article, a newsletter section and a few posts.
- A long report needs a one-page executive summary, or the reverse: notes into a structured document.
- Content must exist in French, English, Spanish or Portuguese, adapted (localised), not word-for-word.
- An internal document must become public: remove internal names, jargon and confidential details.

## How the agent works

1. **Read the source fully** and extract the skeleton: key message, 3 to 7 supporting points, examples, numbers, quotes, call to action.
2. **Define the target:** format, length, audience, reading context (mobile, print, spoken), language and register (tu/vous, formal/informal).
3. **Choose what to keep.** Shorter formats keep the key message and the best example, never all points. Longer formats may expand only with material present in the source or marked for research.
4. **Rewrite natively** for the target: a thread needs a hook and one idea per post; a one-pager needs headings and a decision ask; a translation uses local examples, units, date formats and idioms, and keeps product names and quotes exact.
5. **Fidelity check** (always delivered): numbers and quotes unchanged, nothing added that the source does not support, list of cuts, terms kept in the original language, and passages that need a native speaker's review.

## Documented use cases

### 1. One webinar, five assets
- **Ask Hermes:** "content-transformer: from this webinar transcript, make a 900-word blog post, a newsletter section of 150 words, 3 LinkedIn posts and 5 quotes for slides."
- **What you get:** the five assets, each with its own angle, plus a fidelity table (claims and timestamps in the transcript).

### 2. Localising a landing page into French
- **Ask Hermes:** "Translate and adapt this English landing page for French HR managers, formal 'vous', euros, French date format, keep the product name."
- **What you get:** the French page, adapted examples (French regulations instead of US ones only where the source allows), and a list of sentences flagged for review because the pun does not translate.

### 3. Internal report to public article
- **Ask Hermes:** "Turn this internal retrospective into a public article. Remove client names, internal tools and anything confidential."
- **What you get:** the article, the list of removed elements, and a `content-guardian` scan result showing no personal data left.

## Output format

`TARGET` (format, length, audience, language) · `ASSET(S)` · `FIDELITY CHECK` (kept facts, cuts, changes, open questions) · `REVIEW NOTES` (for a native speaker or an expert).

## Guardrails and limits

- Machine translation of legal, medical or contractual text must be reviewed by a qualified translator.
- Do not transform content you do not have the rights to reuse; quoting stays short and attributed.
- Summaries lose nuance: the fidelity check says which nuance was lost.

## Works well with

`content-creator` (original pieces), `content-guardian` (screen the result), `research-assistant` (verify a claim before it travels to five channels).
