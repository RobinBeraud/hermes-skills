#!/usr/bin/env python3
"""Extract invoice fields from text/PDF files into a ledger-ready CSV.

Standard library only. PDF input needs the optional `pdftotext` binary
(poppler-utils); otherwise convert the PDF to text yourself first.
"""
import argparse, csv, json, os, re, shutil, subprocess, sys, tempfile
from datetime import date

MONTHS = {
    "jan": 1, "janv": 1, "january": 1, "janvier": 1,
    "feb": 2, "fev": 2, "fevr": 2, "february": 2, "fevrier": 2, "février": 2, "févr": 2, "fév": 2,
    "mar": 3, "mars": 3, "march": 3,
    "apr": 4, "avr": 4, "april": 4, "avril": 4,
    "may": 5, "mai": 5,
    "jun": 6, "juin": 6, "june": 6,
    "jul": 7, "juil": 7, "july": 7, "juillet": 7,
    "aug": 8, "aout": 8, "août": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "septembre": 9,
    "oct": 10, "october": 10, "octobre": 10,
    "nov": 11, "november": 11, "novembre": 11,
    "dec": 12, "december": 12, "decembre": 12, "décembre": 12, "déc": 12,
}

DEFAULT_RULES = {
    "Software & subscriptions": ["subscription", "abonnement", "saas", "licence", "license", "hosting", "hébergement", "hebergement", "domain", "cloud"],
    "Travel": ["train", "flight", "airline", "hotel", "hôtel", "taxi", "uber", "sncf", "mileage", "carburant", "fuel"],
    "Meals & entertainment": ["restaurant", "lunch", "dinner", "déjeuner", "dejeuner", "repas", "café", "cafe"],
    "Office supplies": ["stationery", "papeterie", "toner", "paper", "fournitures", "office supplies"],
    "Telecom": ["mobile plan", "internet", "fibre", "telecom", "forfait"],
    "Professional services": ["consulting", "conseil", "honoraires", "freelance", "audit", "legal", "accounting", "comptab", "training", "formation"],
    "Marketing & advertising": ["advertising", "publicité", "publicite", "ads", "campaign", "campagne", "printing", "impression"],
    "Utilities": ["electricity", "électricité", "electricite", "water", "gas", "energy", "énergie"],
    "Insurance": ["insurance", "assurance", "premium"],
}

NUM = r"-?\d{1,3}(?:[ \u00a0\u202f.,]\d{3})*(?:[.,]\d{1,2})?|-?\d+(?:[.,]\d{1,2})?"
CUR = {"€": "EUR", "eur": "EUR", "$": "USD", "usd": "USD", "£": "GBP", "gbp": "GBP", "chf": "CHF"}

NET_LABELS = r"(?:total\s+h\.?t\.?|montant\s+h\.?t\.?|sous[- ]total(?:\s+h\.?t\.?)?|total\s+hors\s+taxes?|net\s+amount|subtotal|sub-total|total\s+excl(?:uding|\.)?\s*(?:vat|tax)|total\s+net|\bH\.?T\b)"
VAT_LABELS = r"(?:t\.?v\.?a\.?(?:\s*\(?\s*[\d.,]+\s*%\s*\)?)?|vat(?:\s*\(?\s*[\d.,]+\s*%\s*\)?)?|sales\s+tax|tax)"
GROSS_LABELS = r"(?:total\s+t\.?t\.?c\.?|montant\s+t\.?t\.?c\.?|net\s+à\s+payer|net\s+a\s+payer|amount\s+due|total\s+due|grand\s+total|total\s+incl(?:uding|\.)?\s*(?:vat|tax)|balance\s+due|total\s+amount|\btotal\b|\bT\.?T\.?C\b)"


def parse_amount(s):
    """Parse '1 234,56', '1,234.56', '1.234,56', '1234.5' into float."""
    s = s.strip().replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if not s:
        return None
    neg = s.startswith("-")
    s = s.lstrip("-")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = head.replace(",", "") + "." + tail if len(tail) <= 2 else s.replace(",", "")
    elif s.count(".") > 1 or ("." in s and len(s.rpartition(".")[2]) == 3 and len(s.partition(".")[0]) <= 3 and False):
        head, _, tail = s.rpartition(".")
        s = head.replace(".", "") + "." + tail if len(tail) <= 2 else s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def amounts_in(line):
    out = []
    for m in re.finditer(NUM, line):
        txt = m.group(0)
        if re.fullmatch(r"-?\d{1,3}", txt) and "%" in line[m.end():m.end() + 2]:
            continue  # a percentage, not an amount
        v = parse_amount(txt)
        if v is not None:
            out.append(v)
    return out


def find_labeled(lines, label_re, exclude_re=None):
    """Return the last amount on the last line matching label_re."""
    found = None
    for ln in lines:
        low = ln.lower()
        if re.search(label_re, low, re.I) and not (exclude_re and re.search(exclude_re, low, re.I)):
            # strip percentages like 'TVA 20%' so the rate is not read as an amount
            clean = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", ln)
            vals = amounts_in(clean)
            if vals:
                found = vals[-1]
    return found


def parse_date(text):
    cands = []
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", text):
        cands.append((m.start(), m.group(1), m.group(2), m.group(3)))
    for m in re.finditer(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4}|\d{2})\b", text):
        y = m.group(3)
        y = "20" + y if len(y) == 2 else y
        cands.append((m.start(), y, m.group(2), m.group(1)))  # day-first
    for m in re.finditer(r"\b(\d{1,2})(?:st|nd|rd|th|er)?\s+([A-Za-zéûôàèç]{3,10})\.?,?\s+(\d{4})\b", text):
        mo = MONTHS.get(m.group(2).lower())
        if mo:
            cands.append((m.start(), m.group(3), str(mo), m.group(1)))
    for m in re.finditer(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", text):
        mo = MONTHS.get(m.group(1).lower())
        if mo:
            cands.append((m.start(), m.group(3), str(mo), m.group(2)))
    valid = []
    for pos, y, mo, d in cands:
        try:
            valid.append((pos, date(int(y), int(mo), int(d)).isoformat()))
        except ValueError:
            pass
    if not valid:
        return None
    # prefer a date next to an invoice/date label
    for pos, iso in sorted(valid):
        ctx = text[max(0, pos - 40):pos].lower()
        if re.search(r"invoice date|date de facture|date d.?émission|date d.?emission|facture du|issued|date\s*:?\s*$", ctx):
            return iso
    return sorted(valid)[0][1]


def parse_invoice_number(text):
    m = re.search(r"(?:invoice|facture)\s*(?:no\.?|n°|number|num[ée]ro|#)?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/_.]{2,})", text, re.I)
    if m:
        cand = m.group(1).rstrip(".")
        if re.search(r"\d", cand):
            return cand
    m = re.search(r"\b(?:no|n°|ref)\.?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/_]{2,})", text, re.I)
    return m.group(1) if m and re.search(r"\d", m.group(1)) else ""


def parse_supplier(lines):
    skip = re.compile(r"^(invoice|facture|bill to|billed to|date|page|tel|phone|email|e-mail|www|http|vat|tva|siret|iban)\b", re.I)
    for ln in lines[:12]:
        t = ln.strip()
        if len(t) < 2 or skip.match(t) or re.fullmatch(r"[\d\W]+", t):
            continue
        return t[:80]
    return ""


def parse_currency(text):
    for sym, code in CUR.items():
        if sym in ("€", "$", "£"):
            if sym in text:
                return code
        elif re.search(r"\b" + sym + r"\b", text, re.I):
            return code
    return ""


def parse_rate(text):
    m = re.search(r"(?:t\.?v\.?a\.?|vat|tax)\D{0,12}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%", text, re.I)
    return parse_amount(m.group(1)) if m else None


def categorize(text, rules):
    low = text.lower()
    best, score = "Uncategorised", 0
    for cat, kws in rules.items():
        s = sum(low.count(k.lower()) for k in kws)
        if s > score:
            best, score = cat, s
    return best


def extract(text, rules, tolerance):
    lines = [l for l in (x.strip() for x in text.splitlines()) if l]
    net = find_labeled(lines, NET_LABELS)
    vat = find_labeled(lines, VAT_LABELS, exclude_re=r"total\s+t\.?t\.?c|incl|n°\s*(?:de\s*)?t\.?v\.?a|vat\s*(?:no|number|id)|tva\s*intra|siret")
    gross = find_labeled(lines, GROSS_LABELS, exclude_re=r"h\.?t\b|excl|hors|sous|sub|net\s+amount|total\s+net")
    rate = parse_rate(text)
    warnings = []

    # fill a missing figure from the other two when possible
    if gross is None and net is not None and vat is not None:
        gross = round(net + vat, 2); warnings.append("gross computed from net+vat")
    if net is None and gross is not None and vat is not None:
        net = round(gross - vat, 2); warnings.append("net computed from gross-vat")
    if vat is None and net is not None and gross is not None:
        vat = round(gross - net, 2); warnings.append("vat computed from gross-net")

    if None in (net, vat, gross):
        warnings.append("could not find all three amounts")
    else:
        if abs(net + vat - gross) > tolerance:
            warnings.append(f"totals mismatch: net {net:.2f} + vat {vat:.2f} = {net+vat:.2f} != gross {gross:.2f}")
        if net:
            real = vat / net * 100
            if rate is not None and abs(real - rate) > 0.6:
                warnings.append(f"stated VAT rate {rate:g}% differs from computed {real:.1f}%")
            if rate is None:
                rate = round(real, 2)
        if net < 0 or gross < 0:
            warnings.append("negative amount (credit note?)")

    inv_date = parse_date(text)
    if not inv_date:
        warnings.append("date not found")
    supplier = parse_supplier(lines)
    if not supplier:
        warnings.append("supplier not found")
    return {
        "supplier": supplier,
        "invoice_number": parse_invoice_number(text),
        "date": inv_date or "",
        "currency": parse_currency(text),
        "net": "" if net is None else f"{net:.2f}",
        "vat": "" if vat is None else f"{vat:.2f}",
        "vat_rate_pct": "" if rate is None else f"{rate:g}",
        "gross": "" if gross is None else f"{gross:.2f}",
        "category": categorize(text, rules),
        "status": "OK" if not warnings or all(w.startswith(("gross computed", "net computed", "vat computed")) for w in warnings) else "REVIEW",
        "warnings": "; ".join(warnings),
    }


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    if path.lower().endswith(".pdf"):
        exe = shutil.which("pdftotext")
        if not exe:
            raise RuntimeError("pdftotext not found (install poppler-utils) or convert the PDF to .txt first")
        r = subprocess.run([exe, "-layout", path, "-"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError("pdftotext failed: " + r.stderr.strip()[:200])
        if not r.stdout.strip():
            raise RuntimeError("PDF has no text layer (scanned image?); OCR it first")
        return r.stdout
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


FIELDS = ["file", "supplier", "invoice_number", "date", "currency", "net", "vat", "vat_rate_pct", "gross", "category", "status", "warnings"]

SAMPLES = {
    "fr.txt": """ACME Hébergement SARL
Facture n° FA-2026-0042
Date de facture : 14/03/2026
Abonnement hébergement cloud - mars   100,00 €
Total HT      1 000,00 €
TVA 20%         200,00 €
Total TTC     1 200,00 €
""",
    "en.txt": """Globex Consulting Ltd
Invoice #INV-7781
Issued: March 5, 2026
Consulting services, 10h
Subtotal $2,500.00
VAT (20%) $500.00
Total due $3,000.00
""",
    "bad.txt": """Initech Print
Invoice No: 55-A
Date: 2026-02-01
Printing flyers
Subtotal 100.00
VAT 20% 20.00
Total 130.00
""",
}


def selftest():
    d = tempfile.mkdtemp()
    for n, t in SAMPLES.items():
        with open(os.path.join(d, n), "w", encoding="utf-8") as f:
            f.write(t)
    rows = {n: extract(read_input(os.path.join(d, n)), DEFAULT_RULES, 0.02) for n in SAMPLES}
    fr, en, bad = rows["fr.txt"], rows["en.txt"], rows["bad.txt"]
    assert (fr["net"], fr["vat"], fr["gross"], fr["date"], fr["invoice_number"]) == ("1000.00", "200.00", "1200.00", "2026-03-14", "FA-2026-0042"), fr
    assert fr["supplier"] == "ACME Hébergement SARL" and fr["status"] == "OK" and fr["currency"] == "EUR", fr
    assert fr["category"] == "Software & subscriptions", fr
    assert (en["net"], en["vat"], en["gross"], en["date"]) == ("2500.00", "500.00", "3000.00", "2026-03-05"), en
    assert en["category"] == "Professional services" and en["currency"] == "USD", en
    assert bad["status"] == "REVIEW" and "mismatch" in bad["warnings"], bad
    assert parse_amount("1.234,56") == 1234.56 and parse_amount("1,234.56") == 1234.56 and parse_amount("1 234,5") == 1234.5
    print("selftest OK (3 sample invoices, amounts/date/category/mismatch checks passed)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="*", help="invoice .txt/.pdf files, or - for stdin")
    ap.add_argument("-o", "--output", help="CSV output path (default: stdout)")
    ap.add_argument("--rules", help="JSON file {category: [keywords]} replacing the default categories")
    ap.add_argument("--tolerance", type=float, default=0.02, help="allowed |net+vat-gross| in currency units (default 0.02)")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter (use ';' for Excel in French locales)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.inputs:
        ap.error("no input files (or use --selftest)")
    rules = DEFAULT_RULES
    if a.rules:
        with open(a.rules, encoding="utf-8") as f:
            rules = json.load(f)
    out = open(a.output, "w", newline="", encoding="utf-8") if a.output else sys.stdout
    w = csv.DictWriter(out, fieldnames=FIELDS, delimiter=a.delimiter)
    w.writeheader()
    review = 0
    for p in a.inputs:
        try:
            row = extract(read_input(p), rules, a.tolerance)
        except Exception as e:
            row = {k: "" for k in FIELDS}
            row.update(status="ERROR", warnings=str(e))
        row["file"] = os.path.basename(p)
        review += row["status"] != "OK"
        w.writerow(row)
    if a.output:
        out.close()
    print(f"{len(a.inputs)} invoice(s) processed, {review} need review", file=sys.stderr)
    return 1 if review else 0


if __name__ == "__main__":
    sys.exit(main())
