#!/usr/bin/env python3
"""depwatch: report outdated dependencies from requirements.txt / package.json.

Uses only the Python standard library and the public PyPI and npm registry
JSON endpoints (no API key). Classifies each update as major / minor / patch
and flags pre-release or unparseable versions instead of guessing.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": "depwatch/1.0 (+hermes skill)"}
VER_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)$")


def parse_version(s):
    """Return (major, minor, patch, suffix) or None."""
    m = VER_RE.match(s.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0), m.group(4) or "")


def classify(current, latest):
    c, l = parse_version(current), parse_version(latest)
    if not c or not l:
        return "unknown"
    if l[3]:
        return "prerelease"
    if l[:3] == c[:3]:
        return "current"
    if l[:3] < c[:3]:
        return "ahead"
    if l[0] > c[0]:
        return "major"
    if l[1] > c[1]:
        return "minor"
    return "patch"


def parse_requirements(text):
    """Yield (name, pinned_version or None). Only '==' pins give a version."""
    out = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        line = line.split(";", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(.*)$", line)
        if not m:
            continue
        name, spec = m.group(1), m.group(3)
        pin = re.search(r"(?:^|,)\s*(?:==|===)\s*([^\s,]+)", spec)
        if not pin:
            pin = re.search(r"~=\s*([^\s,]+)", spec)
        out.append((name, pin.group(1) if pin else None))
    return out


def parse_package_json(text):
    data = json.loads(text)
    out = []
    for key in ("dependencies", "devDependencies"):
        for name, spec in (data.get(key) or {}).items():
            m = re.match(r"^[\^~=v ]*(\d+(?:\.\d+){0,2})$", spec.strip())
            out.append((name, m.group(1) if m else None))
    return out


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def latest_pypi(name):
    return fetch_json("https://pypi.org/pypi/%s/json" % name)["info"]["version"]


def latest_npm(name):
    return fetch_json("https://registry.npmjs.org/%s/latest" % name.replace("/", "%2F"))["version"]


def check(deps, fetcher):
    rows = []
    for name, pinned in deps:
        row = {"name": name, "current": pinned, "latest": None, "status": None}
        try:
            row["latest"] = fetcher(name)
        except urllib.error.HTTPError as e:
            row["status"] = "lookup-failed (HTTP %s)" % e.code
        except Exception as e:  # network, JSON, timeout
            row["status"] = "lookup-failed (%s)" % type(e).__name__
        if row["status"] is None:
            row["status"] = "unpinned" if not pinned else classify(pinned, row["latest"])
        rows.append(row)
    return rows


ORDER = {"major": 0, "minor": 1, "patch": 2, "prerelease": 3, "unknown": 4}


def render(rows):
    rows = sorted(rows, key=lambda r: (ORDER.get(r["status"], 9), r["name"]))
    lines = ["%-28s %-12s %-12s %s" % ("PACKAGE", "PINNED", "LATEST", "STATUS")]
    for r in rows:
        lines.append("%-28s %-12s %-12s %s" % (r["name"], r["current"] or "-", r["latest"] or "-", r["status"]))
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines.append("")
    lines.append("Summary: " + ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    lines.append("Major updates may contain breaking changes: read the changelog before bumping.")
    return "\n".join(lines)


def selftest():
    assert classify("1.2.3", "2.0.0") == "major"
    assert classify("1.2.3", "1.3.0") == "minor"
    assert classify("1.2.3", "1.2.9") == "patch"
    assert classify("1.2.3", "1.2.3") == "current"
    assert classify("2.0.0", "1.9.0") == "ahead"
    assert classify("1.0", "2.0.0rc1") == "prerelease"
    assert classify("abc", "1.0.0") == "unknown"
    req = "requests==2.0.0  # http\nflask>=2.0\n-r other.txt\nnumpy[extra]==1.2.3 ; python_version>'3'\n"
    assert parse_requirements(req) == [("requests", "2.0.0"), ("flask", None), ("numpy", "1.2.3")]
    pj = '{"dependencies":{"a":"^1.2.3","b":"latest"},"devDependencies":{"c":"~0.4"}}'
    assert parse_package_json(pj) == [("a", "1.2.3"), ("b", None), ("c", "0.4")]
    fake = {"requests": "3.0.0", "numpy": "1.2.4", "flask": "3.1.0"}
    def f(n):
        if n not in fake:
            raise KeyError(n)
        return fake[n]
    rows = check(parse_requirements(req) + [("ghost", "1.0.0")], f)
    st = {r["name"]: r["status"] for r in rows}
    assert st["requests"] == "major" and st["numpy"] == "patch" and st["flask"] == "unpinned"
    assert st["ghost"].startswith("lookup-failed")
    print(render(rows))
    print("\nselftest OK")


def main():
    ap = argparse.ArgumentParser(description="Report outdated dependencies from requirements.txt or package.json")
    ap.add_argument("file", nargs="?", help="path to requirements.txt or package.json")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument("--fail-on-major", action="store_true", help="exit 1 if any major update exists")
    ap.add_argument("--selftest", action="store_true", help="run offline tests")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.file:
        ap.error("file is required")
    text = open(a.file, encoding="utf-8").read()
    if a.file.endswith("package.json"):
        deps, fetcher = parse_package_json(text), latest_npm
    else:
        deps, fetcher = parse_requirements(text), latest_pypi
    rows = check(deps, fetcher)
    print(json.dumps(rows, indent=2) if a.json else render(rows))
    return 1 if a.fail_on_major and any(r["status"] == "major" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
