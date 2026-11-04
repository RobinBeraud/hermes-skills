---
name: readme-auditor
description: Audit a README.md with a local script (title, intro, install, usage, code blocks, license, links) and get a 0-100 score plus prioritized fixes; use before publishing or reviewing a repository.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [readme, documentation, lint, audit, open-source]
    category: software-development
    requires_toolsets: [terminal]
---

# README Auditor

Checks a README against a short list of objective criteria and returns a score with findings sorted by severity. The agent then proposes concrete rewrites for each finding.

## When to use

- Before publishing or open-sourcing a repository.
- When reviewing a pull request that touches the README.
- When asked "is this README good?" and you want evidence rather than an impression.
- As a CI gate (`--fail-under`).

## Requirements

- Python 3.8+ (standard library only). No API key.
- `--check-links` needs outbound HTTP access.

## Usage

```bash
# Human-readable report
python3 scripts/readme_audit.py README.md

# JSON for further processing
python3 scripts/readme_audit.py README.md --json

# Also HEAD-request up to 30 http(s) links, flag 404/410
python3 scripts/readme_audit.py README.md --check-links

# CI gate: exit code 1 if score < 80
python3 scripts/readme_audit.py README.md --fail-under 80

# Built-in tests
python3 scripts/readme_audit.py --selftest
```

Workflow for the agent:

1. Run the script on the README and read the findings (high first).
2. Read the README itself; for each finding write a concrete fix (actual text to insert, not generic advice).
3. Do not invent facts about the project (supported versions, license, commands). If information is missing, ask the maintainer or leave a clearly marked placeholder.
4. Re-run the script after edits and report the before/after score.

What is checked: single H1 title, an intro sentence, Install and Usage sections, presence and language tags of fenced code blocks, an install-like command, unclosed code fences, license mention, Contributing and Requirements sections, placeholder text (TODO, FIXME, lorem ipsum, coming soon, WIP), length, skipped heading levels, images without alt text, plain `http://` links, empty link targets, and (optionally) dead links.

## Example output

Run on a tiny README:

```
README score: 49/100  {'words': 17, 'headings': 2, 'code_blocks': 1, 'links': 2}
[HIGH  ] No Install / Getting started section
[MEDIUM] First paragraph is very short; say what it does and for whom
[MEDIUM] No install-like command found in code blocks
[MEDIUM] No license mention
[MEDIUM] Very short (17 words)
[MEDIUM] 1 empty link target(s)
[LOW   ] 1 code block(s) without a language tag
[LOW   ] No Contributing section
[LOW   ] No Requirements / Prerequisites section (versions, OS)
[LOW   ] 1 image(s) without alt text
[LOW   ] 1 plain http:// link(s)
```

## Limits

- Heuristic, English-oriented: section detection matches English heading words (install, usage, license, ...). A README in another language will be penalized unfairly.
- The score measures structure, not truth or writing quality. A README can score 100 and still be wrong.
- Not every project needs every section (a tiny script may not need Contributing); treat low-severity items as suggestions.
- `--check-links` sends HEAD requests; some servers reject HEAD or block bots, so unreachable links are reported as info only and not penalized. Only 404/410 count as dead. Relative links and anchors are not verified.
- Badges are not analyzed.

## Testing

```bash
python3 scripts/readme_audit.py --selftest   # prints: selftest OK (...)
```

Also verified manually: report and JSON output, `--fail-under` exit code 1, missing-file exit code 2, and dead-link detection (404) against a non-existent page on example.com.

Tested on Hermes v0.22.5 on 2026-11-04.
