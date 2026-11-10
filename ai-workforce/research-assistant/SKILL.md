---
name: research-assistant
description: Synthesise research into actionable insights: plan the question, search and read sources (web, papers, open data, your own documents), grade the evidence, separate facts from opinions, and deliver a short brief with citations, confidence levels and recommended actions. Use when a decision needs evidence rather than the first search result.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, synthesis, literature-review, evidence, citations, insights, ai-workforce]
    category: ai-workforce
    related_skills: [trend-watcher, decision-optimizer, content-creator, arxiv, data-intelligence-router, firecrawl]
---

# Research Assistant

The Research Assistant turns scattered information into decisions. It does not stop at summarising: it states the question, looks for evidence on both sides, judges how strong each source is, and ends with what it means for you and what to do next. Every claim carries a citation; every conclusion carries a confidence level.

## When to use

- Before a decision: entering a market, choosing a method, changing a policy, buying a tool.
- To prepare content, a talk or a course on solid ground.
- To make sense of interviews, survey answers or internal documents you already have.
- When two people quote contradicting studies.

## How the agent works

1. **Frame:** the decision behind the question, the scope (period, geography, population), what would change the answer, and the deadline. Turn it into 3 to 5 sub-questions.
2. **Search widely, then narrowly:** general web for the landscape; primary sources next (papers via `arxiv` or open APIs via `data-intelligence-router`, official statistics, standards, company filings); your own files if provided. Use `firecrawl` or the browser to read pages, not just snippets.
3. **Grade each source** on a simple scale: A (systematic review, official statistics, large study), B (peer-reviewed study, reputable report with method), C (expert opinion, case study), D (marketing, anonymous, undated). Note conflicts of interest and dates.
4. **Synthesise by sub-question:** what the evidence says, how strong, where sources disagree and why (different populations, definitions, years).
5. **Deliver insights, not notes:** 3 to 5 findings, each with "so what" for the user, a confidence level (high, medium, low), and the action it suggests. Then the open questions and what would settle them.

## Documented use cases

### 1. Does a four-day week improve productivity?
- **Ask Hermes:** "research-assistant: evidence on four-day weeks for a 60-person software company in France. I must advise the CEO next week."
- **What you get:** a two-page brief: what the trials measured (and what they did not), strength of each source, findings by sub-question (wellbeing, output, customer service), the conditions where it worked, a confidence level, and a pilot design to test it locally.

### 2. Market sizing for a new training offer
- **Ask Hermes:** "How many companies in France could buy an AI agent training for managers? Use official statistics where possible."
- **What you get:** a top-down and bottom-up estimate with each figure sourced (INSEE, Eurostat, industry reports), the assumptions in a table, and the range rather than a single number.

### 3. Synthesising 15 customer interviews
- **Ask Hermes:** "Here are 15 interview notes. What are the recurring problems, how often, and what should we build first?"
- **What you get:** themes with counts and representative (anonymised) quotes, the problems ranked by frequency and severity, and the three opportunities with the evidence behind each.

## Output format

```
Question and decision · Sub-questions
Findings (3-5): finding → so what → confidence → action
Evidence table | claim | source | grade | date | note |
Disagreements and why · Open questions · Sources (full list with links)
```

## Guardrails and limits

- Never invent a citation, a DOI, a statistic or a quote. If no source is found, say so.
- Check dates: an old study on a fast-moving topic is graded down.
- Paywalled sources are cited only for what is visible (abstract, summary).
- Not a substitute for professional advice in medicine, law or finance.

## Works well with

`trend-watcher` (what is emerging), `decision-optimizer` (turn findings into a choice), `content-creator` (turn the brief into an article), and the existing `arxiv`, `data-intelligence-router` and `firecrawl` skills for sources.
