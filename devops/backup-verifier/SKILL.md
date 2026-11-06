---
name: backup-verifier
description: Check that a backup file exists, is recent, is not suspiciously small, and actually decompresses, using one dependency-free Python script. Use when you need a cron-friendly yes/no on whether last night's backup is usable.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [backup, devops, monitoring, integrity, cron]
    category: devops
    requires_toolsets: [terminal]
---

# Backup Verifier

A backup that exists is not a backup that works. This skill runs a small set of checks on the newest file matching a path or glob and reports OK, WARN or FAIL, with an exit code a scheduler can act on.

## When to use

- After a nightly job, to confirm the archive is there, fresh and readable.
- Before a risky migration, to make sure the latest backup is not truncated.
- As a recurring monitor that alerts when a backup silently stops being produced.

## Requirements

- Python 3.8+ (standard library only). No API key, no network.
- Supported formats for full integrity reads: `.tar`, `.tar.gz`/`.tgz`, `.tar.bz2`, `.tar.xz`, `.zip`, `.gz`, `.bz2`, `.xz`. Other formats only get age and size checks (reported as WARN).

## Usage

The script lives at `scripts/backup_verify.py` inside this skill.

```bash
# Newest file matching a glob (quote it so the shell does not expand it)
python3 scripts/backup_verify.py '/backups/db-*.tar.gz'

# A directory: newest regular file inside it
python3 scripts/backup_verify.py /backups/site --max-age-hours 26

# Stricter size rules, JSON output
python3 scripts/backup_verify.py '/backups/db-*.gz' --min-size 1000000 --shrink-ratio 0.7 --json

# Built-in self test (creates and removes temp files)
python3 scripts/backup_verify.py --selftest
```

Checks performed on the newest match:
1. **exists**: at least one file matches.
2. **freshness**: modification time within `--max-age-hours` (default 26).
3. **size**: at least `--min-size` bytes (default 1024); WARN if smaller than `--shrink-ratio` (default 0.5) times the previous backup.
4. **integrity**: the archive is fully read end to end, so truncation or corruption is caught.
5. **checksum**: if `<file>.sha256` exists next to it, the SHA-256 must match.

Exit codes: `0` all OK, `1` warnings, `2` failures. In a Hermes cron job, run the script and report only when the exit code is not 0.

## Example output

```
Backup: /backups/site-2026-11-05.tar.gz
[OK  ] exists    1 file(s) found, newest: site-2026-11-05.tar.gz
[OK  ] freshness newest backup is 0.0 h old (limit 26.0 h)
[OK  ] size      size 45178 bytes (no previous backup to compare)
[OK  ] integrity tar readable, 2 entries
[OK  ] checksum  sha256 matches sidecar file
Result: OK
```

## Limits

- It proves the archive is readable, not that its contents are the right data or that a restore would succeed. Do a real restore test from time to time.
- Only the newest file is checked in depth; older ones are used for the size comparison only.
- Encrypted archives (gpg, age, 7z, rar) are not opened.
- Remote storage (S3, SFTP) is not supported; mount or sync it locally first.
- The sidecar `.sha256` is read as `<hash>  <name>` (first field used), the format `sha256sum` writes.

## Testing

Run `python3 scripts/backup_verify.py --selftest`. It covers a valid tar.gz with checksum, a truncated archive, a stale archive, a missing file, and a zip that shrank versus the previous one. Also run once on a real archive of your own.

Tested on Hermes v0.22.7 on 2026-11-06 (selftest passed, plus manual run on a freshly created tar.gz with sidecar checksum and on a missing path, which exited 2).
