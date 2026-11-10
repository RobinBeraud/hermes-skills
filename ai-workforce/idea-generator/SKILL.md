---
name: idea-generator
description: Run a structured brainstorm that produces many diverse ideas, then converges on a short, scored shortlist with a next step for each. Use when you need options for a product, campaign, workshop, name or problem and want more than the first obvious answers.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [brainstorming, ideation, creativity, innovation, workshop, ai-workforce]
    category: ai-workforce
    related_skills: [product-critic, decision-optimizer, design-prototyper]
---

# Idea Generator

The Idea Generator is the creative member of your AI workforce. Left alone, a language model gives you the five most predictable ideas. This skill forces divergence first (quantity, variety, deliberately odd angles) and convergence second (clustering, scoring, one concrete next step), the way a good facilitator runs a brainstorm.

## When to use

- You need options, not an answer: product features, campaign angles, workshop formats, names, ways to solve a recurring problem.
- The team is stuck on the same two ideas and you want fresh angles.
- You want to prepare a brainstorming workshop and arrive with a seeded idea wall.

## How the agent works

1. **Frame the challenge** as one "How might we…?" question. Ask at most three clarifying questions: who it is for, what success looks like, hard constraints (budget, time, brand, legal). If the user gave enough, skip the questions.
2. **Diverge with five lenses**, at least five ideas each, never filtering yet:
   - *Obvious*: what a competent person would do first (get it out of the way).
   - *SCAMPER*: substitute, combine, adapt, modify, put to other use, eliminate, reverse.
   - *Constraint flip*: "with zero budget", "in one day", "for 100 times more users", "without software".
   - *Analogy*: how another industry solves the same tension (hospitality, games, logistics, healthcare).
   - *Reverse brainstorm*: how could we make the problem worse? Then invert each answer.
3. **Cluster** the 25+ ideas into 4 to 6 themes and name each theme.
4. **Score** each idea from 1 to 5 on impact, effort (5 = easy), and novelty, using the stated success criteria. Show the table.
5. **Shortlist** 3 ideas: a quick win, a bold bet, and a wildcard. For each, give a one-line pitch, the riskiest assumption, and the cheapest test to run this week.

## Documented use cases

### 1. Webinar ideas for a B2B newsletter
- **Context:** a training company wants webinar topics that bring newsletter readers to a paid course.
- **Ask Hermes:** "Use idea-generator: 25 webinar ideas for HR managers, goal is sign-ups to our management course, 45 minutes max, no sales pitch."
- **What you get:** 25 titles across themes (myths, live diagnostics, guest formats, tools), a scored table, and a shortlist such as a quick win ("5 management rituals to drop in 2027, live poll"), a bold bet (a live coaching session on a real attendee case), a wildcard (a 30-minute "management escape game"), each with a test: announce the title to 10% of the list and compare click rates.

### 2. Reducing no-shows at free events
- **Context:** 40% of registrants never show up.
- **Ask Hermes:** "Reverse brainstorm with idea-generator: how could we make no-shows even worse? Then invert."
- **What you get:** inverted ideas such as a calendar file sent at sign-up, a small commitment step (one question to answer before the session), a reminder from the speaker rather than the platform, a replay only for attendees, each scored and with a two-week test plan.

### 3. Naming a new internal tool
- **Ask Hermes:** "idea-generator, 30 names for our internal knowledge assistant. Short, pronounceable in French and English, no existing trademark in software."
- **What you get:** names grouped by theme (mythology, craft, place, verb), a scored shortlist, and a reminder to run a trademark search before adoption (the agent does not do it).

## Output format

```
## How might we …?
### Ideas (26)
**Theme A: …**  1. … 2. …
### Scoring (impact / effort / novelty)
| # | Idea | Impact | Effort | Novelty | Total |
### Shortlist
- Quick win: … | Riskiest assumption: … | Test this week: …
- Bold bet: …
- Wildcard: …
```

## Guardrails and limits

- Generated ideas are starting points. Names, slogans and concepts may already exist: check trademarks and prior art before publishing.
- Scores are judgement calls made from the criteria you gave. Ask Hermes to show its reasoning or re-score with your weights (see `decision-optimizer`).
- Do not paste confidential strategy into a model you do not control.

## Works well with

`product-critic` to stress-test the shortlist, `decision-optimizer` to choose with weighted criteria, `design-prototyper` to turn the winner into something clickable.
