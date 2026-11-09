---
name: dependency-update-watch
description: Check a requirements.txt or package.json against PyPI and the npm registry and report which pinned dependencies have major, minor or patch updates. Use when auditing a project for outdated packages before an upgrade.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [dependencies, python, npm, updates, maintenance]
    category: software-development
    requires_toolsets: [terminal]
---

# Dependency Update Watch

A single-file, standard-library script that reads a dependency manifest, asks the public PyPI / npm registry for the latest version of each package, and ranks the results by how risky the upgrade is (major first).

## When to use

- Before a maintenance sprint: "what is outdated in this project?"
- In CI or a cron job, to fail when a major update appears (`--fail-on-major`).
- To get a quick, ranked list before deciding what to read changelogs for.

## Requirements

- Python 3.8+ (standard library only, no pip install).
- Internet access to `pypi.org` and `registry.npmjs.org` (public endpoints, no API key).

## Usage

```bash
# Python project
python3 scripts/depwatch.py requirements.txt

# Node project (dependencies + devDependencies)
python3 scripts/depwatch.py package.json

# Machine-readable output, and exit code 1 if any major update exists
python3 scripts/depwatch.py package.json --json --fail-on-major

# Offline self-test (no network)
python3 scripts/depwatch.py --selftest
```

How versions are read:
- requirements.txt: `==`, `===` and `~=` give a baseline version. Ranges such as `>=2.0` are reported as `unpinned` (latest is still shown). Options lines (`-r`, `-e`), URLs and comments are skipped.
- package.json: plain versions with an optional `^`, `~` or `=` prefix give a baseline. Tags like `latest`, git URLs and complex ranges are `unpinned`.

Statuses: `major`, `minor`, `patch`, `prerelease`, `unknown`, `current`, `ahead`, `unpinned`, `lookup-failed (...)`.

## Example output

```
PACKAGE                      PINNED       LATEST       STATUS
express                      4.0.0        5.3.0        major
left-pad                     1.0.0        1.3.0        minor

Summary: major=1, minor=1
Major updates may contain breaking changes: read the changelog before bumping.
```

(Versions shown are what the registries returned when tested; they will change over time.)

## Limits

- It compares version numbers only. It does not read changelogs, so it cannot tell you whether an update is actually breaking.
- Semantic versioning is assumed: a "minor" bump can still break projects that do not follow it.
- Only direct dependencies listed in the file are checked, not transitive ones. Lock files (`poetry.lock`, `package-lock.json`) and `pyproject.toml` are not parsed.
- PyPI "latest" is the registry's current default release; it may not be compatible with your Python version.
- Packages are fetched one by one, so very large manifests are slow. No retry or caching.
- Private registries are not supported.

## Testing

1. `python3 scripts/depwatch.py --selftest` should print a table and `selftest OK`.
2. Run it on a small manifest with an old pin (for example `requests==2.0.0`) and confirm a non-`current` status and a non-zero exit with `--fail-on-major` when a major update exists.
3. Add a nonexistent package name and confirm it shows `lookup-failed (HTTP 404)` instead of crashing.

Tested on Hermes v0.23.0 on 2026-11-09 (selftest, live PyPI and npm lookups, 404 handling, `--fail-on-major` exit code).
