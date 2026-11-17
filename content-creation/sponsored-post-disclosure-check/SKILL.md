---
name: sponsored-post-disclosure-check
description: Checks that a sponsored or gifted social post shows the commercial relationship clearly (wording, position, hashtag burying) against an editable rules list; use before publishing any brand collaboration post. Not legal advice.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [sponsorship, disclosure, influencer, social-media, compliance-checklist]
    category: content-creation
    requires_toolsets: [terminal]
---

# Sponsored Post Disclosure Check

Reads a draft post and tells you whether the paid or gifted relationship is easy to see: is there a clear word (not only "#collab"), does it appear early in the text, is it lost in a pile of hashtags, is the brand named. It applies a rules list you can edit. It does not know your country's law or a platform's current policy.

## When to use
- Before publishing a post made with a brand, an affiliate link, a gifted product or a paid partnership.
- When a brand sends its own rules and you want to compare a draft against them.
- To review a batch of past captions for vague wording.

## Requirements
- Python 3 (standard library only). No API key, no network.
- The post text saved in a `.txt` file (the agent can write it for you).

## Usage
1. Save the caption: `post.txt`.
2. Ask the agent for the rules in force. Use the brand's brief, your contract and the platform/authority guidance you were given. If you have none, the built-in defaults are only a starting point: say so in your answer.
3. Run:
```
python3 scripts/disclosure_check.py post.txt --platform instagram --brand Acme
```
4. To use your own rules, dump the defaults, edit the lists and thresholds, and pass them back:
```
python3 scripts/disclosure_check.py --print-rules > rules.json
python3 scripts/disclosure_check.py post.txt --rules rules.json --platform tiktok
```
Rules keys: `clear_terms` (wording that counts), `ambiguous_terms` (wording that does not count alone), `max_position_chars` (per platform, how early the term must appear), `hashtag_block_limit`, `require_brand_mention`. Add terms in your language (for example the local word for "advertising").
5. Use `--json` for machine-readable output. Exit code is 2 on FAIL, 0 otherwise.

Agent instructions:
- Report the verdict and each finding in plain words, then propose a rewritten caption that fixes them, keeping the creator's voice.
- Always keep the MANUAL line: the native paid-partnership label and the contract still need a human check.
- Never say the post is "legal" or "compliant". Say it "passes the rules list used".
- Never suggest hiding, shortening or disguising the disclosure.

## Example output
```
Verdict: WARN
[WARN] late: First clear term '#ad' starts at character 159; the rule says it should appear within the first 125 (instagram).
[WARN] buried: The disclosure hashtag sits inside a block of 7 hashtags, easy to miss.
[INFO] hashtag_only: Disclosure is hashtag-only; a plain sentence is easier to notice.
[MANUAL] native_label: Check by hand: turn on the platform's own paid-partnership label if it exists, and compare with your contract/brief.
Reminder: this is a text check against your rules, not legal advice.
```

## Limits
- Default terms and position limits are editable guesses, not official numbers. Verify them with the platform and your local rules.
- Text only: it cannot see videos, images, spoken disclosure, stickers or the platform label.
- Matching is by words in English by default; other languages need terms added to the rules.
- Cannot tell whether a post actually is sponsored; you declare it.
- Not legal advice.

## Testing
- `python3 scripts/disclosure_check.py --selftest` runs 6 cases (clear, late, vague-only, missing, look-alike hashtag `#advent`, missing brand) and prints `SELFTEST PASSED`.
- Status: tested with the self-test and one sample caption on Hermes (Linux, Python 3), 2026-11-17. Not tested on real platform rules or other languages.
