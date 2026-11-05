---
name: seo-page-audit
description: Audit the on-page SEO of a single URL or local HTML file (title, meta description, headings, canonical, images, links, content length) and get a prioritized fix list, using one stdlib Python script.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [seo, audit, html, on-page, web]
    category: seo
    requires_toolsets: [terminal]
---

# SEO Page Audit

Checks the basic on-page SEO elements of one page and prints issues ranked high / medium / low. No API key, no third-party packages.

## When to use

- Before publishing or after editing a page, to catch missing titles, meta descriptions, H1s or alt text.
- To compare a draft HTML file against a live page.
- To give a quick, repeatable first pass before a deeper manual review.

## Requirements

- Python 3.8+ (standard library only).
- Network access only when auditing a URL. Local `.html` files work offline.
- Script: `scripts/seo_page_audit.py` inside this skill folder.

## Usage

```bash
# Live page
python3 scripts/seo_page_audit.py https://example.com/blog/my-post

# Local file (relative links are counted as internal)
python3 scripts/seo_page_audit.py ./draft.html

# Machine-readable output
python3 scripts/seo_page_audit.py https://example.com/ --json

# Built-in tests
python3 scripts/seo_page_audit.py --selftest
```

Exit codes: `0` no high-priority issue, `1` at least one high issue (handy in CI), `2` the page could not be loaded.

What is checked: title length, meta description presence and length, exactly one non-empty H1, heading level jumps, rel=canonical, `lang`, meta viewport, robots `noindex`, Open Graph tags, image `alt` and width/height, links with no visible text, internal vs external link counts, visible word count, count of JSON-LD blocks.

Workflow for the agent:
1. Run the script on the target and read the issue list.
2. Fix the high items first, then medium, then low.
3. Re-run and confirm the list shrank. Report what remains instead of claiming the page is "optimized".

## Example output

Real run against `https://example.com/`:

```
Title (14): Example Domain
H1: - | headings: 0 | words: 27
Images: 0 | links internal/external: 0/0 | JSON-LD blocks: 0

[HIGH  ] meta-description-missing: No meta description.
[HIGH  ] h1-missing: No <h1>.
[MEDIUM] canonical-missing: No rel=canonical link.
[MEDIUM] no-internal-links: No internal links found.
[MEDIUM] thin-content: About 27 words of visible text; may be thin for a content page.
[LOW   ] title-short: Title is only 14 chars.
[LOW   ] og-missing: No Open Graph tags (link previews).
```

## Limits

- Reads the HTML as served. Content rendered only by JavaScript is not seen.
- The length thresholds (title about 60, description about 160, 300 words) are common rules of thumb, not guarantees about how any search engine behaves.
- Audits one page. It does not check redirects, robots.txt, sitemaps, page speed, backlinks or keyword relevance.
- Word count and "thin content" are heuristics: a short page can be fine for its purpose.
- Fetch is capped at about 3 MB and sends a generic user agent; some sites block scripted requests.

## Testing

Run `python3 scripts/seo_page_audit.py --selftest`: it checks a deliberately bad page, a clean page, a noindex page, and a fetch against a local HTTP server, and prints `selftest OK`.
Also exercised by hand: a local HTML file, `https://example.com/` and a missing file (exit code 2).

Tested on Hermes v0.22.5 on 2026-11-05.
