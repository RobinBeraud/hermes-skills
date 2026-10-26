---
name: env-secrets-scanner
description: Scan a project folder or git-staged files for leaked secrets (.env files, API keys, private keys, passwords in URLs) before committing, with masked output.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [security, git, secrets, pre-commit]
    category: security
    requires_toolsets: [terminal]
---

# Env & Secrets Scanner

A small, offline, standard-library Python scanner that looks for likely secrets before they reach a git history. Findings are masked, so the report itself is safe to paste into a chat or a ticket.

## When to use

- Before `git commit` or `git push` on a new or inherited project.
- When asked "is it safe to publish this repo?"
- As a quick check on a folder before zipping or sharing it.

## Requirements

- Python 3.8+ (standard library only). No API key, no network.
- `git` only if you use `--staged`.

## Usage

The script is `scripts/scan_secrets.py` inside this skill folder.

```bash
# Scan a whole directory (skips .git, node_modules, venvs, build folders)
python3 scripts/scan_secrets.py /path/to/project

# Scan only what is staged for the next commit
python3 scripts/scan_secrets.py /path/to/repo --staged

# Machine-readable output
python3 scripts/scan_secrets.py . --json
```

Exit codes: `0` clean, `1` findings, `2` usage error. This makes it usable as a git pre-commit hook: `python3 scripts/scan_secrets.py . --staged || exit 1`.

What it detects:
- Real `.env` files (but not `.env.example`, `.sample`, `.template`, `.dist`) and key files (`*.pem`, `*.key`, `id_rsa`, ...).
- Private key blocks, AWS access key IDs, GitHub tokens, Slack tokens, Google API keys, live Stripe keys, JWTs.
- Credentials embedded in URLs (`scheme://user:password@host`).
- Assignments such as `password = "..."`, `api_key: ...`, `TOKEN=...` with non-placeholder values.

To silence a deliberate false positive, add `secretscan:ignore` in a comment on that line.

## Example output

```
.env:0  [env-file]  (file name)
.env:1  [generic-assignment]  Zq8*****wR
cfg.py:1  [generic-assignment]  k8J*****41
3 finding(s)
```

When reporting to the user, list file, line and rule only. Never echo a full secret. If something is found, advise: remove it from the file, rotate the credential (it may already be exposed), and add the file to `.gitignore`. If it was already committed, history must be rewritten and the secret rotated regardless.

## Limits

- Pattern based: it will miss secrets with unusual formats and may flag harmless strings. It is a safety net, not a replacement for dedicated scanners.
- Scans the working tree (or the staged file list), not the full git history. For staged files it reads the working-tree copy, which can differ from the staged blob if you edited after `git add`.
- Files over 1 MB and binary files are skipped (only their names are checked).
- Does not verify whether a detected key is still valid.

## Testing

```bash
python3 scripts/scan_secrets.py --selftest
```

The selftest builds fake secrets in a temporary folder and checks that they are found, that example files are ignored, and that output is masked.

Tested on Hermes v0.22.5 on 2026-10-26 (selftest and a real `--staged` run in a throwaway git repo).
