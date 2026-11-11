#!/usr/bin/env python3
"""Score post/video hooks on three explicit criteria (0-10 each).

Criteria
  specificity    concrete details (numbers, named things, a clear situation)
  curiosity      an open question or gap that makes people want the next line
  promise_risk   how likely the hook over-promises (lower is better); if you
                 give --body, also checks the hook is actually backed by it

This is a rule-based first filter, not a prediction of performance.
Standard library only.
"""
import argparse, json, re, sys

VAGUE = {"things", "stuff", "amazing", "incredible", "awesome", "crazy", "insane",
         "best", "secret", "secrets", "hack", "hacks", "tips", "ultimate", "game-changer"}
CLICKBAIT = ["you won't believe", "you wont believe", "doctors hate", "shocking",
             "guaranteed", "100%", "overnight", "no effort", "effortless", "get rich",
             "never fail", "always works", "go viral", "going viral", "instantly",
             "nobody tells you", "they don't want you to know", "changed my life"]
CURIOUS = {"why", "how", "what", "mistake", "mistakes", "instead", "until", "but",
           "didn't", "didnt", "wrong", "stopped", "quit", "almost", "only", "never",
           "before", "after", "actually", "truth"}
UNITS = re.compile(r"\b\d+(\.\d+)?\s?(%|k|m|min|minutes?|hours?|days?|weeks?|months?|years?|"
                   r"seconds?|euros?|dollars?|usd|eur|posts?|videos?|clips?|words?|steps?)\b", re.I)
STOP = set("a an the and or but of to in on for with is are was were be it this that you your "
           "i my we our at as by from how why what do does did not no".split())

def words(text):
    return re.findall(r"[A-Za-z0-9'%$€.-]+", text)

def clamp(x):
    return max(0, min(10, x))

def content_words(text):
    return {w.lower().strip(".'-") for w in re.findall(r"[A-Za-z]{4,}", text)} - STOP

def score(hook, body=None):
    ws = words(hook)
    low = hook.lower()
    n = len(ws)
    notes = []
    # specificity
    s = 3
    if re.search(r"\d", hook): s += 2
    if UNITS.search(hook): s += 2
    if any(w[0].isupper() for w in ws[1:]): s += 1
    if 6 <= n <= 16: s += 1
    elif n > 25: s -= 2; notes.append("too long for a hook")
    elif n < 4: s -= 2; notes.append("too short to be specific")
    vague = [w for w in ws if w.lower() in VAGUE]
    s -= len(vague)
    if vague: notes.append("vague words: " + ", ".join(sorted(set(v.lower() for v in vague))))
    if re.search(r"\b(i|my|we|our)\b", low): s += 1  # first-hand situation
    # curiosity
    c = 2
    if "?" in hook: c += 2
    c += min(4, sum(1 for w in ws if w.lower().strip("'") in CURIOUS))
    if re.search(r"\b(but|instead|until|didn't|didnt|stopped|quit)\b", low): c += 1
    if hook.rstrip().endswith(":"): c += 1
    # promise risk (higher = worse)
    r = 0
    flags = [p for p in CLICKBAIT if p in low]
    r += 3 * len(flags)
    if flags: notes.append("risky phrases: " + ", ".join(flags))
    if re.search(r"\b(everyone|everybody|always|never|nobody)\b", low): r += 1
    if re.search(r"!{2,}|[A-Z]{6,}", hook): r += 1; notes.append("shouting (caps/!!)")
    backed = None
    if body is not None:
        nums = re.findall(r"\d+(?:[.,]\d+)?", hook)
        missing = [x for x in nums if x not in body]
        if missing:
            r += 3; notes.append("number(s) in hook not found in body: " + ", ".join(missing))
        hw = content_words(hook)
        if hw:
            backed = len(hw & content_words(body)) / len(hw)
            if backed < 0.4:
                r += 3; notes.append("body covers only %d%% of the hook's key words" % round(backed * 100))
            elif backed < 0.6:
                r += 1
    s, c, r = clamp(s), clamp(c), clamp(r)
    total = round((s + c + (10 - r)) / 3, 1)
    return {"hook": hook, "specificity": s, "curiosity": c, "promise_risk": r,
            "total": total, "notes": notes}

def load(path):
    src = sys.stdin if path == "-" else open(path, encoding="utf-8")
    lines = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", l).strip() for l in src.read().splitlines()]
    return [l for l in lines if l]

def selftest():
    good = score("I posted every day for 30 days: here is the one change that doubled my saves?",
                 body="Over 30 days I posted every day. The one change was doubling my saves...")
    # 'doubled' vs body: only checks numbers/words; 30 appears in body
    vague = score("Amazing secret hacks nobody tells you!!")
    spec = score("Why my 12 minute video lost viewers at minute 3")
    assert spec["specificity"] > vague["specificity"], (spec, vague)
    assert vague["promise_risk"] >= 4, vague
    assert vague["total"] < spec["total"], (vague, spec)
    bad = score("I made 500 euros in 2 days", body="Here is how I planned my week.")
    assert bad["promise_risk"] >= 3 and any("not found" in n for n in bad["notes"]), bad
    assert 0 <= good["total"] <= 10
    print("selftest OK")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="text file, one hook per line ('-' for stdin)")
    ap.add_argument("--body", help="file with the post/script text, to check the hook is backed by it")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("give a hooks file or use --selftest")
    body = open(a.body, encoding="utf-8").read() if a.body else None
    res = sorted((score(h, body) for h in load(a.file)), key=lambda x: -x["total"])
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False)); return
    for i, x in enumerate(res, 1):
        print("%d. [%.1f] spec %d | curiosity %d | risk %d  %s" %
              (i, x["total"], x["specificity"], x["curiosity"], x["promise_risk"], x["hook"]))
        for n in x["notes"]:
            print("     - " + n)

if __name__ == "__main__":
    main()
