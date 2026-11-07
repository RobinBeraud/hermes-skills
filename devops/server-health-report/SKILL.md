---
name: server-health-report
description: Produce a read-only health report for a Linux server (disk, inodes, memory, swap, load, failed systemd units, pending updates, reboot flag) with an exit code usable in cron. Use when asked "is this box okay?" or to add a quick check to a scheduled job.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, linux, monitoring, health-check, sysadmin]
    category: devops
    requires_toolsets: [terminal]
---

# Server Health Report

A single Python file (standard library only) that inspects the local Linux machine and prints a ranked list of findings, worst first, ending with an overall verdict. It changes nothing on the system.

## When to use

- The user asks whether a server is healthy, why it feels slow, or what to look at first.
- You want a cheap pre-check before a deploy or a maintenance window.
- You need a cron-friendly check: the exit code is 0 (ok), 1 (warnings), 2 (critical).

## Requirements

- Python 3.8+.
- Linux for full output (reads `/proc/meminfo`, `/proc/mounts`, `/proc/uptime`). On macOS, checks that need `/proc` are reported as unavailable or skipped; disk and load still work where the OS allows.
- Optional: `systemctl` (failed units) and `apt` (pending updates). Missing tools are skipped, not errors.
- No API key, no network.

## Usage

```bash
# Human readable report
python3 scripts/health_report.py

# JSON for further processing
python3 scripts/health_report.py --json

# Skip the apt call (faster, avoids touching package tooling)
python3 scripts/health_report.py --skip-updates

# Custom thresholds (percent)
python3 scripts/health_report.py --disk-warn 70 --disk-crit 85 --mem-warn 80 --mem-crit 90

# Use the exit code in a shell condition
python3 scripts/health_report.py --skip-updates || echo "needs attention"
```

Checks performed:
- Disk space and inode usage per real mounted block device (pseudo filesystems and duplicate bind mounts are ignored).
- Memory based on `MemAvailable` (so page cache is not counted as used), and swap.
- 5-minute load average divided by CPU count (warn at 1.0 per CPU, critical at 2.0).
- Uptime (informational).
- Failed systemd units (any failed unit is critical).
- Reboot-required flag (`/var/run/reboot-required`).
- Upgradable apt packages, with a count of those marked security.

When reporting to the user, quote the lines that are WARN or CRIT, say what each means, and suggest the next read-only command to dig deeper (for example `journalctl -u <unit> -n 50` or `du -xh / --max-depth=1`). Do not fix anything without being asked.

## Example output

```
[WARN] reboot: reboot required
[OK  ] memory: 36% used (1402 MiB of 3896 MiB, available counts cache)
[OK  ] disk /: 59% used, 15.8 GiB free
[OK  ] inodes /: 9% used
[OK  ] load: 0.37 0.12 0.04 on 2 CPU(s)
[INFO] uptime: 11.5 days
[OK  ] failed units: none
[INFO] updates: 10 upgradable (0 flagged security); uses local apt cache, may be stale
Overall: WARNINGS
```

## Limits

- Local machine only; there is no SSH mode. To check a remote host, run the script there.
- The updates check reads the local apt cache; it does not run `apt update`, so it can be stale. Only apt-based distributions are covered.
- Load per CPU is a rough signal and ignores container CPU quotas.
- Network filesystems may be slow to stat; a hung mount can delay the report.
- It does not check application-level health, certificates, backups or open ports.
- Tested on Debian/Ubuntu-style Linux only. macOS behavior is untested.

## Testing

```bash
python3 scripts/health_report.py --selftest   # prints "selftest OK"
python3 scripts/health_report.py; echo $?     # real run on the current host
```

The selftest exercises the parsers (meminfo, mounts, systemctl, apt) and threshold logic on synthetic input. Tested on Hermes v0.22.7 on 2026-11-07 (Ubuntu Linux, Python 3), including a real run of the report.
