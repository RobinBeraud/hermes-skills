#!/usr/bin/env python3
"""Scan a directory (or git staged files) for likely secrets before a commit.

Standard library only. Findings never print the full secret: values are masked.
Exit code: 0 = clean, 1 = findings, 2 = usage error.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
ENV_NAMES = re.compile(r"^\.env(\..+)?$")
ENV_SAFE_SUFFIX = (".example", ".sample", ".template", ".dist")
KEY_FILES = re.compile(r"(\.pem|\.key|\.p12|\.pfx|id_rsa|id_ed25519|id_ecdsa)$")
MAX_SIZE = 1_000_000

PATTERNS = [
    ("private-key-block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("stripe-live-key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{16,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("url-with-password", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s:/@]{3,}@[^\s/]+")),
    ("generic-assignment", re.compile(
        r"""(?ix)\b[\w.-]*(?:secret|password|passwd|token|api[_-]?key|private[_-]?key)[\w.-]*\s*[:=]\s*["']?([^\s"'#]{8,})""")),
]
PLACEHOLDER = re.compile(r"(?i)^(your|change|example|xxx|<|\$\{|\$\(|\{\{|todo|dummy|placeholder|fake|test|null|none|\*+$)")


def mask(value):
    if len(value) <= 8:
        return "*" * len(value)
    return value[:3] + "*" * 5 + value[-2:]


def entropy(s):
    if not s:
        return 0.0
    return -sum((s.count(c) / len(s)) * math.log2(s.count(c) / len(s)) for c in set(s))


def is_text(path):
    try:
        with open(path, "rb") as fh:
            return b"\0" not in fh.read(2048)
    except OSError:
        return False


def scan_file(path, rel):
    findings = []
    base = os.path.basename(path)
    if ENV_NAMES.match(base) and not base.endswith(ENV_SAFE_SUFFIX):
        findings.append({"file": rel, "line": 0, "rule": "env-file", "sample": "(file name)"})
    elif KEY_FILES.search(base):
        findings.append({"file": rel, "line": 0, "rule": "key-file", "sample": "(file name)"})
    try:
        if os.path.getsize(path) > MAX_SIZE or not is_text(path):
            return findings
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                if "secretscan:ignore" in line:
                    continue
                for rule, rx in PATTERNS:
                    m = rx.search(line)
                    if not m:
                        continue
                    val = m.group(1) if rule == "generic-assignment" else m.group(0)
                    if rule == "generic-assignment":
                        if PLACEHOLDER.match(val) or (entropy(val) < 3.0 and not re.search(r"\d", val)):
                            continue
                    findings.append({"file": rel, "line": n, "rule": rule, "sample": mask(val)})
                    break
    except OSError:
        pass
    return findings


def staged_files(root):
    out = subprocess.run(["git", "-C", root, "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("not a git repository or git failed: " + out.stderr.strip())
    return [os.path.join(root, p) for p in out.stdout.splitlines() if p]


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def run(root, staged):
    paths = staged_files(root) if staged else walk(root)
    res = []
    for p in paths:
        if os.path.isfile(p):
            res.extend(scan_file(p, os.path.relpath(p, root)))
    return res


def selftest():
    with tempfile.TemporaryDirectory() as d:
        def w(name, text):
            with open(os.path.join(d, name), "w") as fh:
                fh.write(text)
        # fake values assembled at runtime so this file itself stays clean
        w(".env", "A=1\n")
        w(".env.example", "API_KEY=your_key_here\n")
        w("app.py", "aws = '" + "AKIA" + "ABCDEFGHIJKLMNOP" + "'\n"
          "pass" + "word = 'hunter2hunter2X9'\n"
          "token = 'changeme-token'\n"
          "db = '" + "post" + "gres://" + "bob" + ":" + "s3cretpw" + "@" + "db.example" + ".com/app'\n"
          "ok = 'x'  # secretscan:ignore\n")
        w("clean.txt", "nothing to see here\n")
        found = run(d, False)
        rules = sorted(f["rule"] for f in found)
        assert "env-file" in rules, rules
        assert "aws-access-key-id" in rules, rules
        assert "url-with-password" in rules, rules
        assert not any(f["file"] == ".env.example" for f in found), found
        assert not any(f["file"] == "clean.txt" for f in found), found
        assert all("ABCDEFGHIJKLMNOP" not in f["sample"] for f in found), "secret leaked"
        print("selftest OK:", rules)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--staged", action="store_true", help="scan only git-staged files")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not os.path.isdir(a.path):
        print("not a directory: " + a.path, file=sys.stderr)
        return 2
    found = run(a.path, a.staged)
    if a.json:
        print(json.dumps(found, indent=2))
    else:
        for f in found:
            print("%s:%s  [%s]  %s" % (f["file"], f["line"], f["rule"], f["sample"]))
        print("%d finding(s)" % len(found))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
