---
name: ugc-brief-writer
description: Write a clear brief for UGC creators (goal, key messages, do and don't, deliverables, usage rights, disclosure, payment) and check it for gaps and vague wording before sending.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ugc, brief, creators, marketing, collaboration]
    category: marketing
    requires_toolsets: [terminal]
---

# UGC Brief Writer

Turn a few rough notes about a product and a campaign into a one-page brief that a UGC creator can act on without a call. Then run a small checker that flags missing sections and vague wording.

## When to use

- You are a freelancer, brand owner or community manager who hires creators to make videos or photos about a product.
- You are a creator asked for a brief and want to see what a good one contains before you accept work.
- A brief you already have keeps causing questions, late deliveries or disputes about where the content may be used.

## Requirements

- Python 3 (standard library only) for the checker. No API key, no network.
- Your notes: product, audience, what you want people to do after watching, budget or product gift, dates. Fictional or real, but never paste private contact details.

## Usage

1. Ask the user for the missing basics, only what the notes do not already say: product and one-sentence purpose, target audience, platforms, number and length of deliverables, deadline, fee or gift, where and for how long the brand may reuse the content.
2. Write the brief in Markdown with these headings, in this order:
   - `# Objective`: one sentence, one measurable intent (for example "show the mug in a real morning routine"). No promise of sales or views.
   - `## Key messages`: at most three, each one short.
   - `## Do`: concrete requests (show the product in use, mention one feature, film vertically).
   - `## Don't`: claims you cannot support, competitor mentions, banned topics, anything legally risky.
   - `## Deliverables`: count, format, length, resolution, raw files or not.
   - `## Deadline`: first draft date, final date.
   - `## Usage rights`: where (organic posts, paid ads, website, email), which platforms, how long (a number of months), and whether the creator is credited.
   - `## Disclosure`: the creator must label the post as an advertisement using the platform's paid partnership tool and a clear tag such as #ad. Never ask a creator to hide the commercial link.
   - `## Revisions`: number of feedback rounds and turnaround time.
   - `## Payment`: fee or gifted product, payment date, who pays shipping.
3. Save it to a file, for example `/tmp/brief.md`, and run:

```bash
python3 scripts/brief_check.py /tmp/brief.md
```

4. Fix every `[MISSING]` and `[BLOCK]` line, rewrite each `[VAGUE]` phrase with something concrete, then run the check again until it prints `OK`.
5. Give the user the final brief plus a two-line cover message they can send with it.

Style rules for the agent: plain words, short sentences, no invented numbers, no promised results, no mention of audience size you were not given.

## Example output

```
$ python3 scripts/brief_check.py /tmp/brief.md
[MISSING] no section about key messages
[MISSING] no section about deadline
[VAGUE] vague wording: 'be authentic' (say what you mean in concrete terms)
[MISSING] usage rights do not state duration of use
```

After fixes:

```
OK: no problems found
```

Exit code is 1 if anything is `MISSING` or `BLOCK`, otherwise 0.

## Limits

- The checker is a keyword and heading check. It cannot tell whether your content is good, legal in your country, or complete for your contract.
- It looks for English headings and English vague phrases.
- A brief is not a contract. Legal terms about rights and payment should be reviewed by a qualified person.
- Disclosure rules differ by country and platform; the skill only reminds you to ask for a clear label.

## Testing

```bash
python3 scripts/brief_check.py --selftest
```

Expected: `selftest passed`. Also run it on a short sample file and confirm the exit code.

Status: script tested. Tested on Hermes v0.23.1 on 2026-11-21 (selftest and two sample briefs).
