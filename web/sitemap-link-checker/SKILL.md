---
name: sitemap-link-checker
description: Check a website for broken pages and dead outgoing links starting from its sitemap.xml, using one stdlib Python script; use it before a launch, after a migration, or as a periodic health check.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [web, links, sitemap, qa, seo]
    category: web
    requires_toolsets: [terminal]
---

# Sitemap Link Checker

Reads a sitemap (plain, gzip, or a sitemap index), requests every listed URL, and reports pages that return errors or redirect. With `--links` it also opens each page and checks the outgoing links it finds.

## When to use

- After a site migration, redesign, or URL restructure.
- Before announcing a launch, to catch 404s in the sitemap.
- As a recurring check (cron) that exits non-zero when something is broken.
- When a user asks "are there any dead links on my site?"

## Requirements

- Python 3.8+ (standard library only), outbound HTTP access.
- No API key. The target site must publish a sitemap.xml.

## Usage

Script path: `scripts/sitemap_check.py` inside this skill.

```bash
# 1. Check every URL listed in the sitemap
python3 scripts/sitemap_check.py https://example.com/sitemap.xml

# 2. Also check outgoing links found on each page
python3 scripts/sitemap_check.py https://example.com/sitemap.xml --links

# 3. Limit the crawl and get machine-readable output
python3 scripts/sitemap_check.py https://example.com/sitemap.xml --max-urls 50 --json

# 4. Built-in test against a local throwaway server
python3 scripts/sitemap_check.py --selftest
```

Options: `--links`, `--max-urls N` (default 200), `--workers N` (default 8, keep low to be polite), `--json`.

Behavior notes:
- Each URL is requested with HEAD first; if the server answers 403/405/501 or fails, the script retries with GET.
- Redirects are followed and reported as `REDIRECT` (the sitemap should list final URLs).
- Sitemap indexes are followed up to 3 levels deep.
- Exit code is 1 if any broken URL or dead link was found, 0 otherwise.

## Example output

```
Checked 3 sitemap URLs: 1 broken, 1 redirected
  BROKEN 404 http://127.0.0.1:41233/missing
  REDIRECT 301 http://127.0.0.1:41233/old -> http://127.0.0.1:41233/ok
  DEAD LINK 404 http://127.0.0.1:41233/dead-link (on http://127.0.0.1:41233/ok)
```

(Illustrative output from the local self-test server; ports vary.)

## Limits

- Only checks what the sitemap lists; pages missing from the sitemap are not discovered.
- `--links` checks `<a href>` only (not images, scripts, or JavaScript-rendered links), and caps the number of outgoing targets at 5x `--max-urls`.
- Does not respect robots.txt or rate limits beyond the worker count; only run it on sites you are allowed to test.
- Some sites block unknown user agents or return 403/429 to scripts; those show up as broken even if they work in a browser.
- Anchors (`#fragment`) are not verified.
- Sitemaps are read in memory (50 MB cap per file).

## Testing

Run `python3 scripts/sitemap_check.py --selftest`: it starts a local HTTP server with one valid page, one 404, one redirect and one dead link, then asserts all four are reported. Expected last line: `selftest OK`.

Also run against a small public sitemap (for example `https://www.sitemaps.org/sitemap.xml --max-urls 8`): result was 8 URLs checked, 0 broken.

Tested on Hermes v0.22.5 on 2026-11-01 (Python 3.14).
