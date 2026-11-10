#!/usr/bin/env python3
"""First-pass content screening before publishing or before an LLM reads untrusted text.

  guard.py FILE_OR_DIR... [--policy policy.json] [--json] [--fail-on high]
  echo "text" | guard.py -

Flags, with masked excerpts:
  - personal data: e-mail addresses, phone numbers, IBANs (checksum), payment cards (Luhn), French social security numbers
  - secrets: API keys and tokens with known prefixes, private keys
  - prompt injection patterns in content meant for an AI agent ("ignore previous instructions", fake system prompts, ...)
  - your own policy terms: {"blocked": ["term", ...], "review": ["term", ...], "allow_domains": ["example.com"]}
Exit code 1 when a finding reaches --fail-on (default high). This is a filter, not a judge: it routes content to a
human or an LLM review with the reason attached. Standard library only.
"""
import argparse, json, os, re, sys

RULES = [
    ('email', 'medium', 'personal data', re.compile(r'\b[\w.+-]+@([\w-]+\.)+[a-z]{2,}\b', re.I)),
    ('phone', 'medium', 'personal data', re.compile(r'(?<![\w/])(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{1,4}\)?[\s.-]?){2,4}\d{2,4}(?![\w/])')),
    ('iban', 'high', 'personal data', re.compile(r'\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,3})?\b')),
    ('card_number', 'high', 'personal data', re.compile(r'\b(?:\d[ -]?){13,19}\b')),
    ('fr_ssn', 'high', 'personal data', re.compile(r'\b[12]\s?\d{2}\s?(0[1-9]|1[0-2])\s?(\d{2}|2[AB])\s?\d{3}\s?\d{3}(\s?\d{2})?\b')),
    ('secret_token', 'high', 'secret', re.compile(r'\b(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35})\b')),
    ('private_key', 'high', 'secret', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('prompt_injection', 'high', 'manipulation', re.compile(
        r'(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts?)'
        r'|you are now (in )?(developer|dan|jailbreak)|^\s*(system|assistant)\s*:|<\s*/?\s*system\s*>'
        r'|(reveal|print|show) (your|the) (system prompt|instructions|api key)'
        r'|ignore[sz]? (toutes )?les instructions (précédentes|precedentes)', re.I | re.M)),
]


def luhn(digits):
    s, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n > 4 else n * 2
        s += n; alt = not alt
    return s % 10 == 0


def iban_ok(s):
    s = s.replace(' ', '')
    if len(s) < 15:
        return False
    r = s[4:] + s[:4]
    return int(''.join(str(int(c, 36)) for c in r)) % 97 == 1


def mask(s):
    s = s.strip()
    return s[:2] + '*' * max(1, len(s) - 4) + s[-2:] if len(s) > 6 else '*' * len(s)


def scan_text(text, source, policy):
    found = []
    allow = tuple(policy.get('allow_domains', []))
    for i, line in enumerate(text.splitlines(), 1):
        for kind, sev, cat, rx in RULES:
            for m in rx.finditer(line):
                v = m.group(0)
                digits = re.sub(r'\D', '', v)
                if kind == 'card_number' and not (13 <= len(digits) <= 19 and luhn(digits)):
                    continue
                if kind == 'iban' and not iban_ok(v):
                    continue
                if kind == 'phone' and not (9 <= len(digits) <= 15) or (kind == 'phone' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v.strip())):
                    continue
                if kind == 'email' and allow and v.lower().endswith(allow):
                    continue
                found.append({'source': source, 'line': i, 'kind': kind, 'category': cat, 'severity': sev,
                              'excerpt': v if cat == 'manipulation' else mask(v)})
        low = line.lower()
        for sev, key in (('high', 'blocked'), ('medium', 'review')):
            for term in policy.get(key, []):
                if re.search(r'(?<!\w)' + re.escape(term.lower()) + r'(?!\w)', low):
                    found.append({'source': source, 'line': i, 'kind': f'policy_{key}', 'category': 'policy', 'severity': sev, 'excerpt': term})
    # a card number is also a long digit run: drop phone hits on the same line as a card or IBAN
    strong = {(f['line'], f['source']) for f in found if f['kind'] in ('card_number', 'iban', 'fr_ssn')}
    return [f for f in found if not (f['kind'] == 'phone' and (f['line'], f['source']) in strong)]


def iter_inputs(paths):
    for p in paths:
        if p == '-':
            yield '<stdin>', sys.stdin.read()
        elif os.path.isdir(p):
            for dp, dn, fn in os.walk(p):
                dn[:] = [d for d in dn if not d.startswith('.') and d != 'node_modules']
                for f in fn:
                    if f.endswith(('.txt', '.md', '.html', '.csv', '.json', '.eml', '.yml', '.yaml')):
                        fp = os.path.join(dp, f)
                        yield fp, open(fp, encoding='utf-8', errors='replace').read()
        else:
            yield p, open(p, encoding='utf-8', errors='replace').read()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+'); ap.add_argument('--policy'); ap.add_argument('--json', action='store_true')
    ap.add_argument('--fail-on', choices=['medium', 'high', 'never'], default='high')
    a = ap.parse_args()
    policy = json.load(open(a.policy, encoding='utf-8')) if a.policy else {}
    found = [f for src, text in iter_inputs(a.paths) for f in scan_text(text, src, policy)]
    if a.json:
        print(json.dumps(found, indent=2, ensure_ascii=False))
    else:
        if not found:
            print('No finding. Still read it: this filter does not judge tone, facts or context.')
        for f in found:
            print(f"[{f['severity']}] {f['source']}:{f['line']} {f['kind']} ({f['category']}): {f['excerpt']}")
        if found:
            hi = sum(f['severity'] == 'high' for f in found)
            print(f"\n{len(found)} finding(s), {hi} high. Route high findings to a human before publishing or before an agent acts on this content.")
    levels = {'never': 99, 'high': 2, 'medium': 1}
    sys.exit(1 if any({'high': 2, 'medium': 1}[f['severity']] >= levels[a.fail_on] for f in found) else 0)


if __name__ == '__main__':
    main()
