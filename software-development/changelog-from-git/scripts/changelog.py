#!/usr/bin/env python3
"""Generate a grouped Markdown changelog from git history (stdlib only).

Usage:
  changelog.py [--repo DIR] [--from REF] [--to REF] [--title TEXT] [--include-merges]
  changelog.py --selftest
Without --from, the latest tag reachable from --to is used (or the whole history).
"""
import argparse, os, re, subprocess, sys, tempfile, shutil

SEP = "\x1f"
REC = "\x1e"
CC = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<desc>.+)$")
PR = re.compile(r"\(#(\d+)\)|Merge pull request #(\d+)")
GROUPS = [
    ("breaking", "Breaking changes"), ("feat", "Features"), ("fix", "Fixes"),
    ("perf", "Performance"), ("refactor", "Refactoring"), ("docs", "Documentation"),
    ("test", "Tests"), ("build", "Build"), ("ci", "CI"), ("chore", "Chores"),
    ("other", "Other changes"),
]
ALIASES = {"feature": "feat", "bugfix": "fix", "doc": "docs", "tests": "test"}


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("git error: " + r.stderr.strip())
    return r.stdout


def last_tag(repo, to):
    r = subprocess.run(["git", "-C", repo, "describe", "--tags", "--abbrev=0", to],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def collect(repo, frm, to, include_merges):
    rng = f"{frm}..{to}" if frm else to
    fmt = SEP.join(["%h", "%s", "%b"]) + REC
    args = ["log", rng, "--format=" + fmt]
    if not include_merges:
        args.append("--no-merges")
    out = git(repo, *args)
    items = []
    for rec in out.split(REC):
        rec = rec.strip("\n")
        if not rec:
            continue
        h, subj, body = (rec.split(SEP) + ["", ""])[:3]
        items.append(classify(h.strip(), subj.strip(), body))
    return items


def classify(h, subj, body):
    m = CC.match(subj)
    typ, scope, desc, bang = "other", None, subj, False
    if m:
        t = m.group("type").lower()
        t = ALIASES.get(t, t)
        if t in dict(GROUPS):
            typ, scope, desc, bang = t, m.group("scope"), m.group("desc"), bool(m.group("bang"))
    breaking = bang or "BREAKING CHANGE" in body
    pr = PR.search(subj)
    prn = (pr.group(1) or pr.group(2)) if pr else None
    desc = re.sub(r"\s*\(#\d+\)\s*$", "", desc)
    return {"hash": h, "type": typ, "scope": scope, "desc": desc, "breaking": breaking, "pr": prn}


def render(items, title):
    lines = [f"## {title}", ""]
    if not items:
        return "\n".join(lines + ["_No changes._", ""])
    buckets = {k: [] for k, _ in GROUPS}
    for it in items:
        buckets["breaking" if it["breaking"] else it["type"]].append(it)
    for key, label in GROUPS:
        if not buckets[key]:
            continue
        lines.append(f"### {label}")
        for it in buckets[key]:
            scope = f"**{it['scope']}:** " if it["scope"] else ""
            ref = f" (#{it['pr']})" if it["pr"] else ""
            d = it["desc"][:1].upper() + it["desc"][1:] if it["desc"] else it["desc"]
            lines.append(f"- {scope}{d}{ref} [{it['hash']}]")
        lines.append("")
    return "\n".join(lines)


def selftest():
    tmp = tempfile.mkdtemp(prefix="clog_")
    try:
        def g(*a):
            subprocess.run(["git", "-C", tmp, "-c", "user.name=T", "-c", "user.email=t@example.com", *a],
                           check=True, capture_output=True)
        subprocess.run(["git", "init", "-q", tmp], check=True)
        def commit(msg):
            with open(os.path.join(tmp, "f.txt"), "a") as f:
                f.write(msg + "\n")
            g("add", "."); g("commit", "-q", "-m", msg)
        commit("chore: initial"); g("tag", "v1.0.0")
        commit("feat(api): add search endpoint (#12)")
        commit("fix: handle empty input")
        commit("refactor!: rename config keys")
        commit("update the readme")
        commit("docs: clarify install")
        out = render(collect(tmp, last_tag(tmp, "HEAD"), "HEAD", False), "v1.1.0")
        print(out)
        for needle in ["### Breaking changes", "- **api:** Add search endpoint (#12)",
                       "### Fixes", "### Other changes", "### Documentation"]:
            assert needle in out, "missing: " + needle
        assert "Initial" not in out, "tagged commit must be excluded"
        print("SELFTEST OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to", default="HEAD")
    ap.add_argument("--title", default="Unreleased")
    ap.add_argument("--include-merges", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    frm = a.frm or last_tag(a.repo, a.to)
    print(render(collect(a.repo, frm, a.to, a.include_merges), a.title))


if __name__ == "__main__":
    main()
