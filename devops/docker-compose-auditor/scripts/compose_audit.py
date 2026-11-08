#!/usr/bin/env python3
"""Audit a docker-compose file for common security and reliability problems.

Standard library only. Includes a small YAML-subset reader (block maps, block
lists, flow lists/maps, quoted scalars, block scalars). Anchors, merge keys,
tags and multi-document files are NOT supported; the tool warns if it sees them.

Usage:
  compose_audit.py FILE [--json] [--fail-on high|medium|low|never]
  compose_audit.py --selftest
"""
import argparse
import json
import re
import sys

# ---------------------------------------------------------------- YAML subset

class YamlError(Exception):
    pass


def _strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_top(s, sep=","):
    parts, depth, quote, cur = [], 0, None, []
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _find_key_split(text):
    """Index of the ':' that separates key from value, or -1."""
    quote, depth = None, 0
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == ":" and depth == 0 and (i + 1 == len(text) or text[i + 1] == " "):
            return i
    return -1


def _scalar(tok):
    t = tok.strip()
    if t == "":
        return None
    if t[0] == t[-1] and t[0] in "\"'" and len(t) >= 2:
        return t[1:-1]
    if t.startswith("["):
        return [_scalar(x) for x in _split_top(t[1:-1])]
    if t.startswith("{"):
        d = {}
        for item in _split_top(t[1:-1]):
            k = _find_key_split(item.strip())
            if k < 0:
                d[item.strip()] = None
            else:
                it = item.strip()
                d[_scalar(it[:k])] = _scalar(it[k + 1:])
        return d
    low = t.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return float(t)
    return t


def parse_yaml(text):
    lines = []
    for raw in text.splitlines():
        if raw.strip() == "---" and lines:
            raise YamlError("multi-document YAML is not supported")
        s = _strip_comment(raw.replace("\t", "    "))
        if s.strip() and s.strip() != "---":
            lines.append([len(s) - len(s.lstrip(" ")), s.strip(), raw])
    if not lines:
        return {}
    val, idx = _node(lines, 0, lines[0][0])
    if idx < len(lines):
        raise YamlError("unexpected content near: " + lines[idx][1][:60])
    return val


def _block_scalar(lines, i, indent, style):
    buf = []
    while i < len(lines) and lines[i][0] > indent:
        buf.append(lines[i][1])
        i += 1
    return ("\n" if style.startswith("|") else " ").join(buf), i


def _node(lines, i, indent):
    text = lines[i][1]
    if text == "-" or text.startswith("- "):
        return _seq(lines, i, indent)
    if _find_key_split(text) >= 0:
        return _map(lines, i, indent)
    return _scalar(text), i + 1


def _seq(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        text = lines[i][1]
        rest = text[1:].lstrip()
        if not rest:
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                v, i = _node(lines, i + 1, lines[i + 1][0])
            else:
                v, i = None, i + 1
            out.append(v)
            continue
        offset = len(text) - len(rest)
        if _find_key_split(rest) >= 0 and not rest.startswith(("[", "{", '"', "'")):
            lines[i] = [indent + offset, rest, lines[i][2]]
            v, i = _map(lines, i, indent + offset)
        else:
            v, i = _scalar(rest), i + 1
        out.append(v)
    return out, i


def _map(lines, i, indent):
    out = {}
    while i < len(lines) and lines[i][0] == indent:
        text = lines[i][1]
        if text.startswith("- "):
            break
        k = _find_key_split(text)
        if k < 0:
            raise YamlError("expected 'key: value' near: " + text[:60])
        key = _scalar(text[:k])
        rest = text[k + 1:].strip()
        if key == "<<" or rest.startswith(("&", "*", "!")):
            out.setdefault("__unsupported__", []).append(text[:60])
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            out[key], i = _block_scalar(lines, i + 1, indent, rest)
        elif rest == "":
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            if nxt and nxt[0] > indent:
                out[key], i = _node(lines, i + 1, nxt[0])
            elif nxt and nxt[0] == indent and (nxt[1] == "-" or nxt[1].startswith("- ")):
                out[key], i = _seq(lines, i + 1, indent)
            else:
                out[key], i = None, i + 1
        else:
            out[key], i = _scalar(rest), i + 1
    return out, i

# --------------------------------------------------------------------- audit

SEV_ORDER = {"high": 3, "medium": 2, "low": 1, "info": 0}
RISKY_PORTS = {
    3306: "MySQL/MariaDB", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB",
    9200: "Elasticsearch", 11211: "Memcached", 5672: "RabbitMQ", 2375: "Docker API",
    1433: "SQL Server", 5984: "CouchDB", 9042: "Cassandra",
}
DATA_IMAGES = ("postgres", "mysql", "mariadb", "mongo", "redis", "elasticsearch", "influxdb", "clickhouse")
SECRET_NAME = re.compile(r"(PASS(WORD)?|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY|CREDENTIAL)", re.I)
WEAK_VALUES = {"password", "changeme", "admin", "root", "secret", "123456", "test", "example"}
SENSITIVE_HOST_PATHS = ("/", "/etc", "/root", "/var/run/docker.sock", "/run/docker.sock", "/proc", "/sys")


def _env_items(env):
    if isinstance(env, dict):
        return [(str(k), "" if v is None else str(v)) for k, v in env.items()]
    items = []
    for e in env or []:
        e = str(e)
        if "=" in e:
            k, v = e.split("=", 1)
            items.append((k, v))
        else:
            items.append((e, None))  # passed from host environment
    return items


def _port_parts(p):
    """Return (host_ip, host_port, container_port) for a port entry, or None if not published."""
    if isinstance(p, dict):
        if p.get("published") is None:
            return None
        return (str(p.get("host_ip") or ""), str(p["published"]), str(p.get("target", "")))
    s = str(p).split("/")[0]
    parts = s.split(":")
    if len(parts) == 1:
        return None  # container-only port, not published on a fixed host port
    if len(parts) == 2:
        return ("", parts[0], parts[1])
    return (parts[0], parts[1], parts[2])


def _port_int(s):
    m = re.match(r"\d+", s or "")
    return int(m.group()) if m else None


def audit(doc):
    findings = []

    def add(sev, svc, rule, msg):
        findings.append({"severity": sev, "service": svc, "rule": rule, "message": msg})

    if not isinstance(doc, dict) or not isinstance(doc.get("services"), dict):
        add("high", "-", "no-services", "No 'services' mapping found; is this a compose file?")
        return findings
    if "__unsupported__" in doc or any(isinstance(v, dict) and "__unsupported__" in v for v in doc.values()):
        add("info", "-", "yaml-subset", "File uses anchors/aliases/merge keys/tags; the built-in reader skips them, results may be incomplete.")
    if "version" in doc:
        add("info", "-", "obsolete-version", "Top-level 'version' is obsolete in the Compose Specification and ignored by modern Docker Compose.")

    services = doc["services"]
    declared_volumes = set((doc.get("volumes") or {}).keys()) if isinstance(doc.get("volumes"), dict) else set()

    for name, svc in services.items():
        if not isinstance(svc, dict):
            add("medium", name, "bad-service", "Service definition is not a mapping.")
            continue
        image = svc.get("image")
        if image is None and "build" not in svc:
            add("high", name, "no-image", "Service has neither 'image' nor 'build'.")
        if isinstance(image, str) and "@sha256:" not in image:
            last = image.rsplit("/", 1)[-1]
            if ":" not in last:
                add("medium", name, "unpinned-image", f"Image '{image}' has no tag (defaults to latest). Pin a version.")
            elif last.endswith(":latest"):
                add("medium", name, "latest-tag", f"Image '{image}' uses the 'latest' tag. Pin a version.")

        # ports
        for p in svc.get("ports") or []:
            parts = _port_parts(p)
            if not parts:
                continue
            ip, hport, cport = parts
            loopback = ip in ("127.0.0.1", "localhost", "::1", "[::1]")
            hp, cp = _port_int(hport), _port_int(cport)
            risky = RISKY_PORTS.get(cp) or RISKY_PORTS.get(hp)
            if risky and not loopback:
                add("high", name, "exposed-datastore", f"Port {hport}:{cport} ({risky}) is published on all interfaces. Bind to 127.0.0.1 or use an internal network.")
            elif not loopback and not ip:
                add("info", name, "published-port", f"Port {hport}:{cport} is published on all interfaces (0.0.0.0).")

        # secrets in env
        for k, v in _env_items(svc.get("environment")):
            if SECRET_NAME.search(k) and v:
                if re.fullmatch(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", v):
                    continue  # pure reference to a host/.env variable
                weak = v.strip().lower() in WEAK_VALUES
                add("high", name, "inline-secret",
                    f"Environment variable {k} has a literal value" + (" that looks like a default/weak one" if weak else "") +
                    ". Use ${VAR} from an .env file, or Docker secrets.")

        # privileges
        if svc.get("privileged") is True:
            add("high", name, "privileged", "Container runs in privileged mode.")
        if str(svc.get("network_mode", "")).lower() == "host":
            add("medium", name, "host-network", "network_mode: host removes network isolation.")
        for cap in svc.get("cap_add") or []:
            if str(cap).upper() in ("ALL", "SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"):
                add("high" if str(cap).upper() in ("ALL", "SYS_ADMIN") else "medium", name, "dangerous-capability", f"cap_add includes {cap}.")
        if svc.get("pid") == "host":
            add("high", name, "host-pid", "pid: host shares the host process namespace.")

        # volumes
        has_persistent = False
        for v in svc.get("volumes") or []:
            if isinstance(v, dict):
                src, tgt = str(v.get("source", "")), str(v.get("target", ""))
                vtype = v.get("type")
            else:
                bits = str(v).split(":")
                src, tgt = bits[0], (bits[1] if len(bits) > 1 else "")
                vtype = None
            is_path = src.startswith(("/", ".", "~")) or vtype == "bind"
            if is_path:
                has_persistent = True
                norm = src.rstrip("/") or "/"
                if norm in ("/var/run/docker.sock", "/run/docker.sock"):
                    add("high", name, "docker-socket", "Mounts the Docker socket: the container can control the host's Docker.")
                elif norm in SENSITIVE_HOST_PATHS:
                    add("high", name, "sensitive-mount", f"Mounts sensitive host path {src}.")
            elif src:
                has_persistent = True
                if declared_volumes is not None and src not in declared_volumes and not src.startswith("$"):
                    add("medium", name, "undeclared-volume", f"Named volume '{src}' is not declared under top-level 'volumes'.")
        if isinstance(image, str) and any(d in image.lower() for d in DATA_IMAGES) and not has_persistent:
            add("medium", name, "no-data-volume", "Data store without a volume: data is lost when the container is recreated.")

        # reliability
        if "restart" not in svc and "deploy" not in svc:
            add("low", name, "no-restart", "No restart policy; the service stays down after a crash or reboot.")
        if "healthcheck" not in svc:
            add("low", name, "no-healthcheck", "No healthcheck defined.")

        # depends_on
        dep = svc.get("depends_on")
        deps = list(dep.keys()) if isinstance(dep, dict) else (dep or [])
        for d in deps:
            if d not in services:
                add("high", name, "bad-depends-on", f"depends_on references unknown service '{d}'.")

    findings.sort(key=lambda f: (-SEV_ORDER[f["severity"]], f["service"], f["rule"]))
    return findings

# ----------------------------------------------------------------------- CLI

SAMPLE = """\
version: "3.8"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    depends_on:
      - db
      - cache
  db:
    image: postgres:16
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: changeme
      POSTGRES_USER: app
  app:
    image: example/app:1.4.2
    restart: always
    privileged: true
    environment:
      - API_TOKEN=${API_TOKEN}
      - SESSION_SECRET=abc123
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - data:/data
    healthcheck:
      test: ["CMD", "true"]
"""


def selftest():
    f = audit(parse_yaml(SAMPLE))
    rules = {(x["service"], x["rule"]) for x in f}
    expected = {
        ("web", "latest-tag"), ("web", "no-restart"), ("web", "bad-depends-on"),
        ("db", "exposed-datastore"), ("db", "inline-secret"), ("db", "no-data-volume"),
        ("app", "privileged"), ("app", "docker-socket"), ("app", "inline-secret"),
        ("app", "undeclared-volume"), ("-", "obsolete-version"),
    }
    missing = expected - rules
    assert not missing, f"missing findings: {missing}"
    # ${API_TOKEN} reference must NOT be flagged
    assert not any(x["rule"] == "inline-secret" and "API_TOKEN" in x["message"] for x in f)
    # parser sanity
    d = parse_yaml("a:\n  - x: 1\n    y: [1, 2]\n  - 'z:q'\nb: {k: v}\nc: |\n  l1\n  l2\n")
    assert d == {"a": [{"x": 1, "y": [1, 2]}, "z:q"], "b": {"k": "v"}, "c": "l1\nl2"}, d
    print("selftest OK (%d findings on sample)" % len(f))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit a docker-compose file.")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--fail-on", default="high", choices=["high", "medium", "low", "never"],
                    help="exit 1 if a finding of at least this severity exists (default: high)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    if not a.file:
        ap.error("FILE required (or use --selftest)")
    try:
        with open(a.file, encoding="utf-8") as fh:
            doc = parse_yaml(fh.read())
    except (OSError, YamlError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    findings = audit(doc)
    if a.json:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            print("[%-6s] %-10s %-20s %s" % (f["severity"].upper(), f["service"], f["rule"], f["message"]))
        counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEV_ORDER}
        print("\nSummary: " + ", ".join("%d %s" % (counts[s], s) for s in SEV_ORDER))
    if a.fail_on != "never" and any(SEV_ORDER[f["severity"]] >= SEV_ORDER[a.fail_on] for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
