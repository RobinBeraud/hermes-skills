---
name: design-prototyper
description: Turn a rough concept into a testable prototype: a one-page design brief, user flow, wireframe-level screens and a single self-contained clickable HTML file, plus a five-user test script. Use when an idea needs to be shown and tested before anyone builds it.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [prototyping, ux, design, wireframe, html, user-testing, ai-workforce]
    category: ai-workforce
    related_skills: [idea-generator, product-critic, journey-personalizer]
---

# Design Prototyper

The Design Prototyper refines a concept into something people can click. It works at the fidelity that answers the question at hand: a flow on paper is enough to test the order of steps, a clickable HTML file is needed to test wording and layout. It never jumps to polished visuals before the flow is right.

## When to use

- An idea survived a brainstorm and you want to show it to users or stakeholders this week.
- A form, onboarding or checkout feels clumsy and you want to test an alternative.
- You need a visual spec to hand to a developer or a no-code tool.

## How the agent works

1. **Brief (one page):** target user, the job they want done, success metric, constraints (device, brand colours, accessibility level), and what is out of scope.
2. **Flow:** the happy path in 3 to 7 steps, then the two most likely detours (error, going back, missing data). Written as a numbered list or a Mermaid flowchart.
3. **Screens:** for each step, the content in priority order (heading, key action, supporting info), with real copy, not lorem ipsum.
4. **Clickable prototype:** one HTML file with inline CSS and a few lines of JavaScript to move between screens. No external dependency, works offline, mobile-first, WCAG AA contrast, labelled form fields, visible focus. Save it as `prototype.html` and open it in a browser.
5. **Test script:** five tasks phrased as goals ("You want to…"), what to observe, and the success criterion per task. Five users find most usability problems of a flow.
6. **Iterate:** after feedback, list the issues by severity and produce version 2 with a short changelog.

## Documented use cases

### 1. Course booking in three steps
- **Ask Hermes:** "design-prototyper: a mobile booking flow for a 2-day training: choose a session, attendee details, pay or request a quote for the company. Brand colour #ba348d."
- **What you get:** a brief, a 3-step flow plus the "my company pays" detour, `prototype.html` with four screens and a progress bar, and a test script (for example "Book a seat for a colleague and get an invoice in your company name").

### 2. Redesigning a confusing settings page
- **Context:** support tickets say users cannot find how to change the billing e-mail.
- **Ask Hermes:** "Here is the current settings page (pasted HTML). Prototype a clearer version and a test to compare both."
- **What you get:** a card-sort style regrouping of settings, a new layout in HTML, and an A/B task test: time to find "billing e-mail" on version A vs B.

### 3. Pitching a feature internally
- **Ask Hermes:** "Make a 4-screen clickable demo of the 'weekly digest' idea for Thursday's product review."
- **What you get:** a demo with fake but plausible data, speaker notes per screen, and the open questions to ask the room.

## Output format

1. `BRIEF` (bullets) 2. `FLOW` (numbered steps or Mermaid) 3. `SCREENS` (per step: content in order) 4. `prototype.html` (file) 5. `TEST SCRIPT` (5 tasks with success criteria) 6. `NEXT` (what to learn from the test).

## Guardrails and limits

- A prototype is a question, not a product: no real payment, no real personal data, no back end. Label it "Prototype" on every screen.
- It does not replace a designer for brand work or a developer for production code.
- Check accessibility with real assistive technology before claiming compliance.

## Works well with

`idea-generator` upstream, `product-critic` for a heuristic review before user tests, `engagement-assessor` once a version is live.
