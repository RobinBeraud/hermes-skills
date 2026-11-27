---
name: newsletter-subject-tester
description: Generate several honest subject-line options for a newsletter issue, score them against explicit written criteria, and flag misleading or pushy wording; use before sending any email issue.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [newsletter, email, subject-line, copywriting, marketing]
    category: marketing
    requires_toolsets: [terminal]
---

# Newsletter Subject Tester

Turns "I'll just use the title of my post" into a short, deliberate choice between several honest subject lines, each scored on criteria you can read and argue with.

## When to use

- You finished a newsletter issue and need a subject line (and a preview text).
- You already have a few subject ideas and want a second opinion before sending.
- You want to catch accidental clickbait, fake urgency or spam-like wording.

## Requirements

- Python 3 (standard library only), for the optional checker script.
- No API key, no network access.
- The issue content (paste it, or give a file path) and, if known, the audience and tone.

## Usage

### Step 1: Read the issue first

Ask the user for the issue text if not provided. Write down, in one sentence each: the main promise of the issue, the single most concrete detail (a number from the text, a name of a tool, a result), and who it is for. Only use facts that appear in the text.

### Step 2: Write 8 candidates, in different styles

Produce two of each, all true to the issue:

1. Plain statement of what is inside.
2. A concrete detail from the text (only a number or fact that really appears in it).
3. A question the reader actually has.
4. A short, curiosity-based line that still names the topic.

For each, also propose a preview text (40 to 90 characters) that adds information rather than repeating the subject.

### Step 3: Run the checker

Save the candidates, one per line, in a file and run:

```bash
python3 scripts/subject_check.py candidates.txt
python3 scripts/subject_check.py --subject "Three edits that made my intro shorter"
python3 scripts/subject_check.py candidates.txt --json
```

Useful options: `--max-len 50` (stricter length), `--min-len 20`, `--selftest`.

The script flags: very long or very short lines, mostly-capital text, several ALL-CAPS words, repeated `!` or `?`, pushy phrases (such as "click here" or "act now"), a fake `Re:` or `Fwd:` prefix, an urgency claim with no real date or time, too many emojis, generic subjects ("Newsletter"), and near-duplicate candidates.

### Step 4: Score by hand on the same criteria

For every candidate that survives, give 0 to 2 points on each criterion and show the table:

- Clarity: could a reader say what the email is about?
- Honesty: does the issue deliver exactly what the subject promises?
- Specificity: is there a concrete detail rather than a vague adjective?
- Fit: does it sound like the sender's usual voice?

Add the totals, explain ties in one line, and recommend one main subject plus one alternate. Say clearly that scores are a judgment call, not a prediction of open rates.

### Step 5: Suggest a real A/B test, if the list allows

If the sender's tool supports split tests, suggest testing the top two subjects on equal random halves and keeping a note of the winner and why. Do not claim in advance which will win.

## Example output

```
1. [OK  ] (38 chars) Three edits that made my intro shorter
2. [WARN] (27 chars) FREE GIFT!!! Click here NOW
     - mostly capital letters
     - repeated ! or ?
     - pushy phrases: click here
3. [WARN] (32 chars) Last chance to join the workshop
     - urgency claim without a real date or time: only use if the deadline is true, and name it
1/3 without warnings
```

Recommendation (agent, after manual scoring):

- Main: "Three edits that made my intro shorter" (clear 2/2, honest 2/2, specific 2/2, fit 1/2)
- Alternate: "Is your intro too long? Three quick edits"
- Preview text: "Before and after examples from last week's video script."

## Limits

- The checker uses simple rules (length, capitals, a short list of pushy phrases, regular expressions for dates). It does not understand meaning and will miss subtle clickbait and flag some harmless lines.
- The length limit of 60 characters is a rule of thumb, not a guarantee of what any mail app shows.
- It cannot predict open rates. Only a real split test measures that.
- The emoji check covers common emoji ranges only.
- English-language phrases only; for other languages, rely on the manual steps.
- The skill refuses to propose fake urgency, fake replies or promises the issue does not keep.

## Testing

```bash
python3 scripts/subject_check.py --selftest
```

Expected output: `selftest OK`. Then run the checker on a small file containing both a good and a spammy subject and confirm the second gets warnings.

Status: tested (script). The candidate-writing steps are instructions for the agent and were not benchmarked.

Tested on Hermes v0.23.1 on 2026-11-27.
