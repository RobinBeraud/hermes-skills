---
name: docker-compose-auditor
description: Audit a docker-compose.yml for exposed databases, inline secrets, privileged containers, unpinned images, missing restart policies and healthchecks, using one dependency-free Python script. Use before deploying or reviewing a compose stack.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [docker, compose, security, audit, devops]
    category: devops
    requires_toolsets: [terminal]
---

# Docker Compose Auditor

Static review of a `docker-compose.yml` / `compose.yaml`. It reads the file only; it never starts containers and never contacts a network.

## When to use

- Before deploying or sharing a compose stack.
- When reviewing a stack someone else wrote.
- As a quick CI gate (non-zero exit code on serious findings).

## Requirements

- Python 3.8+ (standard library only, no PyYAML needed).
- The script is `scripts/compose_audit.py` in this skill folder.

## Usage

```bash
# Human-readable report
python3 scripts/compose_audit.py docker-compose.yml

# JSON, for further processing
python3 scripts/compose_audit.py docker-compose.yml --json

# Stricter gate: fail (exit 1) on medium or higher
python3 scripts/compose_audit.py docker-compose.yml --fail-on medium

# Never fail, just report
python3 scripts/compose_audit.py docker-compose.yml --fail-on never
```

Exit codes: 0 = nothing at or above the threshold (default threshold: high), 1 = findings at or above it, 2 = file unreadable or YAML not understood.

Checks performed, per service:

- **high**: datastore ports (PostgreSQL, MySQL, Redis, MongoDB, Elasticsearch, etc.) published on all interfaces; literal values for variables named like PASSWORD, SECRET, TOKEN, API_KEY; `privileged: true`; Docker socket mounted; sensitive host paths mounted (`/`, `/etc`, `/root`, `/proc`, `/sys`); `cap_add` of ALL or SYS_ADMIN; `pid: host`; `depends_on` pointing to a service that does not exist; service with neither `image` nor `build`.
- **medium**: image without tag or with `:latest`; `network_mode: host`; named volume not declared at top level; database image without any volume; NET_ADMIN / SYS_PTRACE capabilities.
- **low**: no `restart` policy; no `healthcheck`.
- **info**: ports published on 0.0.0.0, obsolete top-level `version:`.

A value such as `${DB_PASSWORD}` is treated as a safe reference, not an inline secret.

When reporting to a user, list findings grouped by service, explain the fix in one line each, and offer a corrected snippet only for what was flagged.

## Example output

```
[HIGH  ] app        docker-socket        Mounts the Docker socket: the container can control the host's Docker.
[HIGH  ] db         exposed-datastore    Port 5432:5432 (PostgreSQL) is published on all interfaces. Bind to 127.0.0.1 or use an internal network.
[MEDIUM] web        latest-tag           Image 'nginx:latest' uses the 'latest' tag. Pin a version.
[LOW   ] web        no-restart           No restart policy; the service stays down after a crash or reboot.

Summary: 6 high, 3 medium, 3 low, 2 info
```

## Limits

- The YAML reader covers the subset used by typical compose files: block maps and lists, flow lists/maps, quoted values, block scalars. Anchors, aliases, merge keys (`<<`), tags and multi-document files are not supported; an info finding is raised when they are seen and results may be incomplete.
- `extends`, `include`, profiles and `.env` interpolation are not resolved. Only the single file given is checked.
- Heuristics: secret detection is name-based, so a harmless variable named `TOKEN_TTL` with a literal value will be flagged, and a secret stored under an innocuous name will be missed.
- Does not scan images for vulnerabilities and does not check Dockerfiles.
- Port checks treat a bare host binding (no IP) as all interfaces; a host firewall may still protect it.

## Testing

```bash
python3 scripts/compose_audit.py --selftest
```

Prints `selftest OK` when the parser and all rules behave as expected on a built-in sample (it also checks that `${VAR}` references are not flagged).

Status: tested. Tested on Hermes v0.23.0 on 2026-11-08 (selftest, a sample file with 14 findings and exit code 1, and a clean file with exit code 0, using Python 3.14).
