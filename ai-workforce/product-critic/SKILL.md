---
name: product-critic
description: Evaluate creative and product work (landing page, deck, article, design, prototype, offer, feature) with a structured rubric, specific evidence-based feedback ranked by impact, and concrete rewrites, never vague praise or generic advice. Use before publishing, pitching or building, when you want an honest second opinion.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [critique, review, feedback, ux-review, copy-review, quality, ai-workforce]
    category: ai-workforce
    related_skills: [design-prototyper, content-creator, idea-generator, decision-optimizer]
---

# Product Critic

The Product Critic evaluates creative works with constructive, detailed feedback. It behaves like a senior reviewer who respects the author: it states what works and why, then the few problems that matter most, each tied to a specific place in the work, with a concrete fix. It does not rewrite your work in its own taste, and it does not hide problems behind compliments.

## When to use

- A landing page, sales deck, article, newsletter or course outline is about to go out.
- A prototype or feature spec needs a heuristic review before user testing.
- An offer or pricing page does not convert and you want to know why.
- You want to compare two versions on the same criteria.

## How the agent works

1. **Clarify intent:** who it is for, the one action or belief it should produce, the context of use, and the kind of feedback wanted (big picture or line edit).
2. **Pick the rubric** that fits the work, scored 1 to 5 with evidence:
   - *Message*: clarity in 5 seconds, value proposition, proof, call to action.
   - *Audience fit*: their words, their problem, objections answered.
   - *Structure*: order, scannability, length, one idea per section.
   - *Craft*: copy quality, visual hierarchy, consistency; for interfaces, Nielsen's usability heuristics; accessibility basics (contrast, labels, alt text).
   - *Credibility*: sourced claims, real testimonials, no overpromise.
3. **Find the top 3 issues by impact,** each with: where (quote or element), why it hurts the goal, a concrete fix (rewritten line or layout change), and the effort.
4. **Keep what works,** explicitly, so the author does not break it in the next version.
5. **One question** the author should answer before the next iteration, and an optional quick test (five-second test, show to two target users).

## Documented use cases

### 1. Landing page for a training course
- **Ask Hermes:** "product-critic: review this course page for HR managers. Goal: request the programme PDF."
- **What you get:** scores per criterion, the top 3 fixes (for example "the headline names the method, not the benefit: try 'Your managers lead without micromanaging in 2 days'"; "the form asks 7 fields for a PDF: keep e-mail and company"), what to keep, and a five-second test plan.

### 2. Investor or sales deck
- **Ask Hermes:** "Critique this 12-slide deck as a sceptical buyer. Where would you stop listening?"
- **What you get:** the slide where attention drops and why, missing proof, a reordered storyline, and two slides to cut.

### 3. Comparing two article drafts
- **Ask Hermes:** "Which of these two intros is stronger for busy managers, and why?"
- **What you get:** side-by-side scores, the winning intro, and the one element of the other worth keeping.

## Output format

```
Verdict (2 lines) · Scores | criterion | 1-5 | evidence |
Top 3 issues: where / why / fix / effort
Keep: …   Question for the author: …   Quick test: …
```

## Guardrails and limits

- Feedback targets the work, never the person.
- The critic does not know your market as well as your customers do: validate big claims with real users.
- Taste is not a criterion: every remark must link to the stated goal and audience.

## Works well with

`design-prototyper` and `content-creator` (iterate after the critique), `idea-generator` (when the critique says "wrong idea", not "wrong execution"), `decision-optimizer` (choose between versions).
