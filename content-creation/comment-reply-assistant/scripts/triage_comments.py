#!/usr/bin/env python3
"""Sort a comment export into question / praise / criticism / spam / other.

Reads a CSV (any column holding the comment text) or a plain text file with one
comment per line. Writes a reply sheet (CSV) with an empty "draft_reply" column
and a short Markdown summary. Rule based, standard library only, English and
French keywords. It is a first pass: a human checks the result.

Usage:
  triage_comments.py comments.csv --out reply_sheet.csv
  triage_comments.py comments.txt --summary
  triage_comments.py --selftest
"""
import argparse
import csv
import io
import re
import sys
from collections import Counter

TEXT_COLUMNS = ["comment", "comments", "text", "commentaire", "message", "body", "content", "comment text"]
AUTHOR_COLUMNS = ["author", "username", "user", "name", "auteur", "pseudo", "display name"]

QUESTION_WORDS = (
    r"how|what|why|when|where|which|who|can you|could you|do you|did you|is it|are you|will you|would you|"
    r"comment|pourquoi|quand|où|ou est|quel|quelle|quels|quelles|qui|peux-tu|pouvez-vous|est-ce que|est ce que|tu peux"
)
QUESTION_RE = re.compile(r"\?|^\s*(%s)\b" % QUESTION_WORDS, re.I)

PRAISE_WORDS = [
    "love", "great", "amazing", "awesome", "thank", "thanks", "helpful", "perfect", "brilliant", "well done",
    "nice", "best video", "learned", "super", "génial", "genial", "merci", "bravo", "excellent", "top",
    "très utile", "tres utile", "j'adore", "j'ai adoré", "parfait", "bien expliqué",
]
CRITIC_WORDS = [
    "wrong", "incorrect", "misleading", "disagree", "boring", "waste of time", "too long", "too fast",
    "clickbait", "not true", "bad", "worst", "useless", "didn't work", "doesn't work", "does not work",
    "faux", "nul", "décevant", "decevant", "pas d'accord", "trompeur", "trop long", "trop rapide",
    "ça ne marche pas", "ca ne marche pas", "perte de temps", "mensonge",
]
SPAM_PATTERNS = [
    r"https?://", r"www\.", r"\b\w+\.(com|net|io|ru|xyz|biz)\b", r"sub4sub", r"sub for sub",
    r"check (out )?my (channel|profile|page)", r"follow me", r"dm me", r"whats ?app\s*\+?\d",
    r"\+\d{8,}", r"giveaway winner", r"crypto", r"forex", r"earn \$?\d+", r"make money", r"gagne[rz]? de l'argent",
    r"abonne[- ]toi", r"promo code", r"click (the )?link",
]
SPAM_RE = re.compile("|".join(SPAM_PATTERNS), re.I)
ABUSE_WORDS = ["idiot", "stupid", "shut up", "hate you", "kill", "ta gueule", "imbécile", "imbecile", "connard"]


def classify(text):
    """Return (category, reasons, needs_care)."""
    t = text.strip()
    low = t.lower()
    reasons = []
    if not t:
        return "other", ["empty"], False
    if SPAM_RE.search(t):
        reasons.append("contains link / promo pattern")
        return "spam", reasons, False
    letters = [c for c in t if c.isalpha()]
    if len(t) > 12 and letters and sum(c.isupper() for c in letters) / len(letters) > 0.8 and "!" in t:
        reasons.append("mostly capitals")
    abusive = any(w in low for w in ABUSE_WORDS)
    critic_hits = [w for w in CRITIC_WORDS if w in low]
    praise_hits = [w for w in PRAISE_WORDS if re.search(r"\b%s" % re.escape(w), low)]
    is_q = bool(QUESTION_RE.search(t))
    if abusive:
        return "criticism", ["abusive wording: do not engage without a human"], True
    if critic_hits:
        reasons.append("negative wording: " + ", ".join(critic_hits[:3]))
        if is_q:
            reasons.append("also a question")
        return "criticism", reasons, True
    if is_q:
        reasons.append("question mark or question opener")
        if praise_hits:
            reasons.append("also positive")
        return "question", reasons, False
    if praise_hits:
        return "praise", ["positive wording: " + ", ".join(praise_hits[:3])], False
    return "other", ["no strong signal"], False


def read_comments(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    if path.lower().endswith((".csv", ".tsv")):
        dialect = csv.excel_tab if path.lower().endswith(".tsv") else csv.excel
        rows = list(csv.DictReader(io.StringIO(raw), dialect=dialect))
        if not rows:
            return []
        cols = {c.lower().strip(): c for c in rows[0].keys() if c}
        text_col = next((cols[c] for c in TEXT_COLUMNS if c in cols), None)
        if text_col is None:
            raise SystemExit("No comment column found. Columns seen: %s. Rename one to 'comment'." % ", ".join(rows[0].keys()))
        auth_col = next((cols[c] for c in AUTHOR_COLUMNS if c in cols), None)
        return [((r.get(auth_col) or "") if auth_col else "", (r.get(text_col) or "").strip()) for r in rows]
    return [("", line.strip()) for line in raw.splitlines() if line.strip()]


def triage(comments):
    out = []
    seen = Counter(c[1].lower() for c in comments)
    for i, (author, text) in enumerate(comments, 1):
        cat, reasons, care = classify(text)
        if seen[text.lower()] > 1 and len(text) >= 20 and cat != "spam":
            cat, reasons = "spam", ["identical text posted %d times" % seen[text.lower()]]
        out.append({"id": i, "author": author, "comment": text, "category": cat,
                    "reason": "; ".join(reasons), "needs_human_care": "yes" if care else "no",
                    "draft_reply": "", "status": "draft"})
    return out


def summary(rows):
    n = Counter(r["category"] for r in rows)
    lines = ["# Comment triage", "", "Total comments: %d" % len(rows)]
    for k in ("question", "praise", "criticism", "spam", "other"):
        lines.append("- %s: %d" % (k, n.get(k, 0)))
    care = [r for r in rows if r["needs_human_care"] == "yes"]
    lines.append("- needing extra care: %d" % len(care))
    return "\n".join(lines)


def selftest():
    sample = [
        ("a", "How do you edit these so fast?"),
        ("b", "Love this, thank you!"),
        ("c", "This is wrong and misleading."),
        ("d", "Check out my channel https://example.com/x"),
        ("e", "Nice"),
        ("f", "Nice"),
        ("i", "Please visit my page for amazing news"),
        ("j", "Please visit my page for amazing news"),
        ("g", "Pourquoi tu n'utilises pas un micro?"),
        ("h", "ok"),
    ]
    rows = triage(sample)
    got = [r["category"] for r in rows]
    want = ["question", "praise", "criticism", "spam", "praise", "praise", "spam", "spam", "question", "other"]
    assert got == want, (got, want)
    assert rows[2]["needs_human_care"] == "yes"
    print(summary(rows))
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--out", help="write the reply sheet CSV here")
    ap.add_argument("--summary", action="store_true", help="print the Markdown summary")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        ap.error("give a comments file or --selftest")
    rows = triage(read_comments(a.file))
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"])
            w.writeheader()
            w.writerows(rows)
        print("Wrote %d rows to %s" % (len(rows), a.out))
    if a.summary or not a.out:
        print(summary(rows))
        if not a.out:
            for r in rows:
                print("%3d [%s] %s" % (r["id"], r["category"], r["comment"][:80]))


if __name__ == "__main__":
    sys.exit(main())
