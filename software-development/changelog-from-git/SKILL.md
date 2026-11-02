---
name: changelog-from-git
description: Generate a readable, grouped Markdown changelog from git history (Conventional Commits aware, PR numbers kept) between two refs; use when preparing release notes.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, changelog, release-notes, conventional-commits]
    category: software-development
    requires_toolsets: [terminal]
---

# Changelog from Git

Turns the commit log between two refs into release notes grouped by type (features, fixes, docs...), with breaking changes surfaced first.

## When to use
- You are cutting a release and need notes from the commits since the last tag.
- You want a quick "what changed between v1.2 and main" summary.
- You want to check how well a repo follows Conventional Commits (commits that do not match land in "Other changes").

## Requirements
- `git` and Python 3 (standard library only). No API key, no network.
- Run it against a local clone.

## Usage
```bash
# Since the latest tag reachable from HEAD (whole history if no tag exists)
python3 scripts/changelog.py --repo /path/to/repo --title "v1.4.0"

# Explicit range
python3 scripts/changelog.py --repo . --from v1.3.0 --to main --title "v1.4.0"

# Keep merge commits (default: skipped)
python3 scripts/changelog.py --from v1.3.0 --include-merges

# Built-in check
python3 scripts/changelog.py --selftest
```
Recognised prefixes: feat, fix, perf, refactor, docs, test, build, ci, chore (plus aliases feature, bugfix, doc, tests). `type(scope)!:` or a `BREAKING CHANGE` footer puts the entry under "Breaking changes". A trailing `(#123)` or a `Merge pull request #123` subject is kept as a PR reference.

## Example output
```
## v1.1.0

### Breaking changes
- Rename config keys [7825a14]

### Features
- **api:** Add search endpoint (#12) [609795f]

### Fixes
- Handle empty input [291d6d7]

### Other changes
- Update the readme [4441e7d]
```
Redirect to a file (`> CHANGES.md`) and review it before publishing.

## Limits
- It only reads commit subjects and bodies; it does not call the GitHub/GitLab API, so PR titles that differ from commit subjects are not used.
- With squash-merge workflows the PR number appears only if it is in the subject.
- Squashed history or non-conventional messages give a long "Other changes" section: the tool does not guess types.
- Output is Markdown only, no commit links or author names.

## Testing
Run `python3 scripts/changelog.py --selftest`: it builds a throwaway repo in a temp directory, makes commits of each kind after a tag, and asserts on the grouped output (prints `SELFTEST OK`). A second manual check on a one-commit repo without tags returned the whole history.
Tested on Hermes (cron agent run) on 2026-11-02.
