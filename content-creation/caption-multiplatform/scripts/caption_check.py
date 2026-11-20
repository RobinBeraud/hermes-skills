#!/usr/bin/env python3
"""Check platform-adapted captions against editable limits.

Input: a text/markdown file where each caption starts with a heading line
like "## instagram" followed by the caption text.
Limits live in a JSON file you can edit (defaults below are starting values:
verify them against each platform's current help pages).
"""
import argparse, json, re, sys

DEFAULT_LIMITS = {
    "instagram": {"max_chars": 2200, "max_hashtags": 30, "preview_chars": 125},
    "tiktok":    {"max_chars": 2200, "max_hashtags": 10, "preview_chars": 80},
    "linkedin":  {"max_chars": 3000, "max_hashtags": 5,  "preview_chars": 140},
    "youtube":   {"max_chars": 5000, "max_hashtags": 15, "preview_chars": 100},
}
DISCLOSURE = re.compile(r"#(ad|sponsored|partner|paidpartnership)\b|\b(ad|sponsored|paid partnership|gifted)\b", re.I)
CTA = re.compile(r"\b(comment|follow|subscribe|save|share|link|read|watch|reply|tell me|vote|join|sign up|download|try)\b", re.I)


def parse(text):
    parts, name, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s*([A-Za-z0-9 _-]+?)\s*$", line)
        if m:
            if name is not None:
                parts[name] = "\n".join(buf).strip()
            name, buf = m.group(1).strip().lower(), []
        elif name is not None:
            buf.append(line)
    if name is not None:
        parts[name] = "\n".join(buf).strip()
    return parts


def check(name, body, limits, sponsored=False):
    lim = limits.get(name)
    issues, info = [], {}
    n = len(body)
    tags = re.findall(r"(?<!\w)#\w+", body)
    first = body.strip().split("\n")[0] if body.strip() else ""
    info.update(chars=n, hashtags=len(tags), first_line_chars=len(first))
    if not body.strip():
        issues.append("caption is empty")
        return info, issues
    if lim is None:
        issues.append(f"no limits defined for '{name}' (add it to the limits file)")
    else:
        if n > lim["max_chars"]:
            issues.append(f"too long: {n} > {lim['max_chars']} characters")
        if len(tags) > lim["max_hashtags"]:
            issues.append(f"too many hashtags: {len(tags)} > {lim['max_hashtags']}")
        if len(first) > lim["preview_chars"]:
            issues.append(f"first line is {len(first)} chars; only about {lim['preview_chars']} may show before the cut-off")
    if not CTA.search(body):
        issues.append("no call to action found")
    letters = [c for c in first if c.isalpha()]
    if len(letters) > 8 and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        issues.append("first line is mostly capitals")
    if sponsored and not DISCLOSURE.search(body):
        issues.append("sponsored content but no disclosure wording (e.g. #ad) found")
    return info, issues


def run(path, limits_path, sponsored):
    limits = DEFAULT_LIMITS
    if limits_path:
        with open(limits_path, encoding="utf-8") as f:
            limits = json.load(f)
    with open(path, encoding="utf-8") as f:
        parts = parse(f.read())
    if not parts:
        print("No '## platform' sections found.")
        return 2
    bad = 0
    for name, body in parts.items():
        info, issues = check(name, body, limits, sponsored)
        print(f"[{name}] {info['chars']} chars, {info['hashtags']} hashtags, first line {info['first_line_chars']} chars")
        for i in issues:
            print(f"  - {i}")
        if not issues:
            print("  OK")
        bad += bool(issues)
    return 1 if bad else 0


def selftest():
    good = "## instagram\nThree things I learned editing my first video.\nSave this for later. #editing #video\n"
    p = parse(good)
    info, issues = check("instagram", p["instagram"], DEFAULT_LIMITS)
    assert not issues, issues
    long_ = "x" * 2300 + " follow"
    _, issues = check("instagram", long_, DEFAULT_LIMITS)
    assert any("too long" in i for i in issues)
    _, issues = check("linkedin", "Nice product. Read more at example.com", DEFAULT_LIMITS, sponsored=True)
    assert any("disclosure" in i for i in issues)
    _, issues = check("linkedin", "Nice product #ad. Read more", DEFAULT_LIMITS, sponsored=True)
    assert not any("disclosure" in i for i in issues)
    _, issues = check("mastodon", "hello follow", DEFAULT_LIMITS)
    assert any("no limits" in i for i in issues)
    print("selftest OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--limits", help="JSON file overriding the default limits")
    ap.add_argument("--sponsored", action="store_true", help="require disclosure wording")
    ap.add_argument("--dump-limits", action="store_true", help="print default limits as JSON")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.dump_limits:
        print(json.dumps(DEFAULT_LIMITS, indent=2)); sys.exit(0)
    if not a.file:
        ap.error("file required")
    sys.exit(run(a.file, a.limits, a.sponsored))
