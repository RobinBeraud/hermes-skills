#!/usr/bin/env python3
"""Audit a README.md: structure, install, usage examples, links, length.

Usage:
  readme_audit.py README.md [--json] [--check-links]
  readme_audit.py --selftest
Standard library only. Exit code 0 always unless file unreadable (2),
or --fail-under N is given and the score is below N (1).
"""
import argparse, json, re, sys, urllib.request, urllib.error

def parse(text):
    lines = text.splitlines()
    headings, in_code, fences = [], False, 0
    code_blocks, cur, lang = [], [], ""
    for i, l in enumerate(lines):
        if l.strip().startswith("```"):
            if in_code:
                code_blocks.append((lang, "\n".join(cur)))
                cur, in_code = [], False
            else:
                in_code, lang = True, l.strip()[3:].strip()
                fences += 1
            continue
        if in_code:
            cur.append(l)
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", l)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip(), i + 1))
    return lines, headings, code_blocks, in_code

def has_heading(headings, words):
    return any(re.search(w, h[1], re.I) for h in headings for w in words)

def audit(text, check_links=False):
    lines, headings, blocks, unclosed = parse(text)
    findings = []  # (severity, message)
    score = 100
    def add(sev, msg, pen):
        nonlocal score
        findings.append((sev, msg)); score -= pen

    if not text.strip():
        return 0, [("high", "README is empty")], {}
    h1 = [h for h in headings if h[0] == 1]
    if not h1:
        add("high", "No top-level title (# Title)", 15)
    elif len(h1) > 1:
        add("low", f"{len(h1)} H1 headings; use a single title", 3)
    # first paragraph = description
    body = [l for l in lines if l.strip() and not l.lstrip().startswith(("#", "!", "[", "<", "```", "|", "-", "*"))]
    if not body:
        add("high", "No introductory sentence explaining what the project does", 15)
    elif len(body[0].split()) < 6:
        add("medium", "First paragraph is very short; say what it does and for whom", 5)
    if not has_heading(headings, [r"install", r"getting started", r"setup", r"quick ?start"]):
        add("high", "No Install / Getting started section", 15)
    if not has_heading(headings, [r"usage", r"example", r"quick ?start", r"how to"]):
        add("high", "No Usage / Examples section", 15)
    if not blocks:
        add("high", "No fenced code blocks: readers cannot copy a command", 10)
    else:
        untyped = sum(1 for lang, _ in blocks if not lang)
        if untyped:
            add("low", f"{untyped} code block(s) without a language tag", 2)
        if not any(re.search(r"(pip|npm|yarn|pnpm|cargo|go (get|install)|brew|apt|gem|docker|git clone|make)\b", c) for _, c in blocks):
            add("medium", "No install-like command found in code blocks", 5)
    if unclosed:
        add("high", "Unclosed code fence: the rest of the file renders as code", 10)
    if not has_heading(headings, [r"licen[sc]e"]) and not re.search(r"\blicen[sc]e\b", text, re.I):
        add("medium", "No license mention", 5)
    if not has_heading(headings, [r"contribut"]):
        add("low", "No Contributing section", 2)
    if not has_heading(headings, [r"requirement", r"prerequisite", r"depend", r"support"]):
        add("low", "No Requirements / Prerequisites section (versions, OS)", 3)
    if re.search(r"\b(TODO|FIXME|lorem ipsum|coming soon|WIP)\b", text, re.I):
        add("medium", "Placeholder text found (TODO / FIXME / lorem / coming soon / WIP)", 4)
    words = len(text.split())
    if words < 80:
        add("medium", f"Very short ({words} words)", 8)
    elif words > 4000:
        add("low", f"Very long ({words} words); consider splitting into docs/", 3)
    # skipped heading levels
    prev = 0
    for lvl, title, ln in headings:
        if prev and lvl > prev + 1:
            add("low", f"Line {ln}: heading level jumps from H{prev} to H{lvl}", 1)
            break
        prev = lvl
    # images without alt text
    noalt = len(re.findall(r"!\[\]\(", text))
    if noalt:
        add("low", f"{noalt} image(s) without alt text", 2)
    # links
    links = re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", text)
    http = sorted({l for l in links if l.startswith(("http://", "https://"))})
    insecure = [l for l in http if l.startswith("http://")]
    if insecure:
        add("low", f"{len(insecure)} plain http:// link(s)", 1)
    empty = [l for l in links if l in ("#", "")]
    if empty:
        add("medium", f"{len(empty)} empty link target(s)", 3)
    if check_links:
        for u in http[:30]:
            try:
                req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "readme-audit/1.0"})
                urllib.request.urlopen(req, timeout=8)
            except urllib.error.HTTPError as e:
                if e.code in (404, 410):
                    add("medium", f"Dead link ({e.code}): {u}", 3)
            except Exception:
                findings.append(("info", f"Could not reach (not counted): {u}"))
    stats = {"words": words, "headings": len(headings), "code_blocks": len(blocks), "links": len(links)}
    return max(score, 0), findings, stats

def selftest():
    good = """# Tool
Tool converts widgets into gadgets quickly for small teams on any platform.

## Requirements
Python 3.8+

## Install
```bash
pip install tool
```

## Usage
```bash
tool run input.txt
```
Some more explanation here to make the document long enough to count as real documentation
for readers who want to know what it does, how it behaves on errors, and what output to expect
when running it against a typical input file in a normal project directory on their machine.

## Contributing
Open a PR.

## License
MIT
"""
    bad = "# A\n# B\nTODO\n```\nrm x\n"
    s1, f1, _ = audit(good)
    s2, f2, _ = audit(bad)
    assert s1 >= 95, (s1, f1)
    assert s2 < 40, (s2, f2)
    assert any("Unclosed" in m for _, m in f2)
    assert audit("")[0] == 0
    print(f"selftest OK (good={s1}, bad={s2})")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check-links", action="store_true", help="HEAD-request up to 30 http(s) links")
    ap.add_argument("--fail-under", type=int, help="exit 1 if score below N")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.path:
        ap.error("path required")
    try:
        text = open(a.path, encoding="utf-8").read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr); sys.exit(2)
    score, findings, stats = audit(text, a.check_links)
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    findings.sort(key=lambda f: order[f[0]])
    if a.json:
        print(json.dumps({"score": score, "stats": stats,
                          "findings": [{"severity": s, "message": m} for s, m in findings]}, indent=2))
    else:
        print(f"README score: {score}/100  {stats}")
        for s, m in findings:
            print(f"[{s.upper():6}] {m}")
        if not findings:
            print("No issues found.")
    if a.fail_under is not None and score < a.fail_under:
        sys.exit(1)

if __name__ == "__main__":
    main()
