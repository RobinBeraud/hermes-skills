#!/usr/bin/env python3
"""Flip margin calculator: projected profit of a buy-renovate-resell operation.

Standard library only. All figures are assumptions supplied by the user;
nothing here is tax, legal or investment advice.
"""
import argparse
import json
import sys

DEFAULTS = {
    "purchase_price": None,        # required
    "resale_price": None,          # required
    "works_budget": 0.0,
    "works_contingency_pct": 10.0,  # placeholder assumption: extra % on works
    "acquisition_fees_pct": 7.5,    # placeholder: purchase taxes/notary/legal, % of price
    "other_acquisition_costs": 0.0, # fixed amount (surveys, diagnostics...)
    "holding_months": 6.0,
    "monthly_carrying_costs": 0.0,  # property tax, insurance, utilities, per month
    "resale_fees_pct": 4.0,         # placeholder: agent/legal fees on resale, % of resale price
    "loan_ltc_pct": 0.0,            # loan as % of (purchase + works incl. contingency)
    "loan_rate_pct": 4.0,           # annual nominal rate
    "loan_fees": 0.0,               # fixed amount (file fees, guarantee)
    "loan_type": "interest_only",   # interest_only | amortizing
    "loan_term_months": 240,        # only used for amortizing
}


def validate(p):
    for k in ("purchase_price", "resale_price"):
        if p.get(k) is None or p[k] <= 0:
            raise ValueError(f"{k} is required and must be > 0")
    for k, v in p.items():
        if k == "loan_type":
            if v not in ("interest_only", "amortizing"):
                raise ValueError("loan_type must be interest_only or amortizing")
        elif v is not None and v < 0:
            raise ValueError(f"{k} must be >= 0")
    if p["loan_ltc_pct"] > 100:
        raise ValueError("loan_ltc_pct cannot exceed 100")
    if p["loan_type"] == "amortizing" and p["loan_term_months"] <= 0:
        raise ValueError("loan_term_months must be > 0")


def interest_paid(principal, annual_pct, months, kind, term):
    """Total interest paid over `months` (may be fractional; rounded up to whole payments)."""
    if principal <= 0 or annual_pct <= 0:
        return 0.0, principal
    r = annual_pct / 100.0 / 12.0
    n = int(-(-months // 1))  # ceil
    if kind == "interest_only":
        return principal * r * n, principal
    pay = principal * r / (1 - (1 + r) ** (-term))
    bal, total = principal, 0.0
    for _ in range(min(n, int(term))):
        i = bal * r
        total += i
        bal -= pay - i
    return total, max(bal, 0.0)


def compute(p):
    validate(p)
    works = p["works_budget"] * (1 + p["works_contingency_pct"] / 100.0)
    acq = p["purchase_price"] * p["acquisition_fees_pct"] / 100.0 + p["other_acquisition_costs"]
    carry = p["monthly_carrying_costs"] * p["holding_months"]
    resale_fees = p["resale_price"] * p["resale_fees_pct"] / 100.0
    loan = (p["purchase_price"] + works) * p["loan_ltc_pct"] / 100.0
    interest, balance = interest_paid(loan, p["loan_rate_pct"], p["holding_months"],
                                      p["loan_type"], p["loan_term_months"])
    loan_fees = p["loan_fees"] if loan > 0 else 0.0
    total_cost = (p["purchase_price"] + works + acq + carry + resale_fees + interest + loan_fees)
    profit = p["resale_price"] - total_cost
    outlay_before_sale = p["purchase_price"] + works + acq + carry + interest + loan_fees
    equity = max(outlay_before_sale - loan, 0.0)  # simplification: all costs funded up front
    roi = profit / equity * 100 if equity > 0 else None
    months = p["holding_months"]
    annualized = None
    if roi is not None and months > 0 and roi > -100:
        annualized = ((1 + roi / 100.0) ** (12.0 / months) - 1) * 100
    return {
        "works_with_contingency": works,
        "acquisition_costs": acq,
        "carrying_costs": carry,
        "resale_fees": resale_fees,
        "loan_amount": loan,
        "loan_interest": interest,
        "loan_fees": loan_fees,
        "loan_balance_repaid_at_sale": balance,
        "total_cost": total_cost,
        "net_profit_before_tax": profit,
        "margin_on_resale_pct": profit / p["resale_price"] * 100,
        "margin_on_cost_pct": profit / total_cost * 100,
        "equity_invested": equity,
        "roi_on_equity_pct": roi,
        "annualized_roi_pct": annualized,
    }


def solve(p, field, target_profit, lo, hi):
    """Bisection: find value of `field` (purchase_price or resale_price) giving target profit."""
    def f(x):
        q = dict(p); q[field] = x
        return compute(q)["net_profit_before_tax"] - target_profit
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        fm = f(mid)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def sensitivity(p):
    rows = []
    for dp in (-10, -5, 0, 5):
        for dw in (0, 10, 20):
            q = dict(p)
            q["resale_price"] = p["resale_price"] * (1 + dp / 100.0)
            q["works_budget"] = p["works_budget"] * (1 + dw / 100.0)
            rows.append((dp, dw, compute(q)["net_profit_before_tax"]))
    return rows


def money(x):
    return f"{x:,.0f}"


def report(p, target_margin):
    r = compute(p)
    out = []
    out.append("ASSUMPTIONS (every value is editable; untouched defaults are placeholders, not facts)")
    for k in DEFAULTS:
        out.append(f"  {k} = {p[k]}")
    out.append("")
    out.append("COSTS")
    out.append(f"  purchase price            {money(p['purchase_price'])}")
    out.append(f"  works (with contingency)  {money(r['works_with_contingency'])}")
    out.append(f"  acquisition costs         {money(r['acquisition_costs'])}")
    out.append(f"  carrying costs            {money(r['carrying_costs'])}")
    out.append(f"  loan interest + fees      {money(r['loan_interest'] + r['loan_fees'])}")
    out.append(f"  resale fees               {money(r['resale_fees'])}")
    out.append(f"  TOTAL COST                {money(r['total_cost'])}")
    out.append("")
    out.append("RESULT (before any tax)")
    out.append(f"  resale price              {money(p['resale_price'])}")
    out.append(f"  net profit                {money(r['net_profit_before_tax'])}")
    out.append(f"  margin on resale price    {r['margin_on_resale_pct']:.1f}%")
    out.append(f"  margin on total cost      {r['margin_on_cost_pct']:.1f}%")
    out.append(f"  equity invested           {money(r['equity_invested'])}")
    if r["roi_on_equity_pct"] is not None:
        out.append(f"  ROI on equity             {r['roi_on_equity_pct']:.1f}%")
    if r["annualized_roi_pct"] is not None:
        out.append(f"  annualized ROI            {r['annualized_roi_pct']:.1f}%")
    be = solve(p, "resale_price", 0.0, 1.0, p["resale_price"] * 5)
    if be is not None:
        out.append(f"  break-even resale price   {money(be)}")
    if target_margin is not None:
        # target margin on resale price: profit = margin * resale ; solve on purchase price
        def gap(x):
            q = dict(p); q["purchase_price"] = x
            c = compute(q)
            return c["net_profit_before_tax"] - target_margin / 100.0 * q["resale_price"]
        lo, hi = 1.0, p["resale_price"]
        if gap(lo) * gap(hi) <= 0:
            for _ in range(100):
                mid = (lo + hi) / 2
                if gap(lo) * gap(mid) <= 0:
                    hi = mid
                else:
                    lo = mid
            out.append(f"  max purchase price for {target_margin:g}% margin on resale: {money((lo + hi) / 2)}")
        else:
            out.append(f"  target margin {target_margin:g}% not reachable with these assumptions")
    out.append("")
    out.append("SENSITIVITY: net profit by resale price change (rows) and works overrun (columns)")
    out.append("  resale \\ works   +0%        +10%       +20%")
    rows = sensitivity(p)
    for i in range(0, len(rows), 3):
        dp = rows[i][0]
        out.append(f"  {dp:+4d}%         " + "  ".join(f"{money(v):>9}" for _, _, v in rows[i:i + 3]))
    out.append("")
    out.append("Not tax, legal or investment advice. Figures are only as good as your inputs.")
    return "\n".join(out)


def selftest():
    p = dict(DEFAULTS)
    p.update(purchase_price=200000, resale_price=300000, works_budget=40000,
             works_contingency_pct=0, acquisition_fees_pct=0, resale_fees_pct=0,
             holding_months=6, monthly_carrying_costs=500)
    r = compute(p)
    assert abs(r["net_profit_before_tax"] - (300000 - 200000 - 40000 - 3000)) < 1e-6, r
    # interest only: 100000 loan at 6% for 6 months = 3000
    p2 = dict(p, loan_ltc_pct=100 * 100000 / 240000, loan_rate_pct=6.0)
    r2 = compute(p2)
    assert abs(r2["loan_interest"] - 3000) < 1e-6, r2
    assert abs(r2["net_profit_before_tax"] - (57000 - 3000)) < 1e-6
    # break-even resale price equals total cost
    be = solve(p, "resale_price", 0.0, 1.0, 1e7)
    assert abs(be - 243000) < 1e-3, be
    # solved purchase price hits target profit
    sp = solve(p, "purchase_price", 30000, 1.0, 300000)
    q = dict(p, purchase_price=sp)
    assert abs(compute(q)["net_profit_before_tax"] - 30000) < 1e-3
    # amortizing interest is lower than interest-only for same principal
    p3 = dict(p2, loan_type="amortizing", loan_term_months=240)
    assert compute(p3)["loan_interest"] < r2["loan_interest"]
    # validation
    try:
        compute(dict(p, purchase_price=0)); raise SystemExit("validation failed")
    except ValueError:
        pass
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", help="JSON file with assumptions")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true", help="print raw results as JSON")
    ap.add_argument("--target-margin", type=float,
                    help="target net margin on resale price (%%); prints max purchase price")
    for k, v in DEFAULTS.items():
        if k == "loan_type":
            ap.add_argument("--loan-type", dest=k, choices=["interest_only", "amortizing"])
        else:
            ap.add_argument("--" + k.replace("_", "-"), dest=k, type=float)
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    p = dict(DEFAULTS)
    if a.config:
        with open(a.config) as fh:
            cfg = json.load(fh)
        unknown = set(cfg) - set(DEFAULTS)
        if unknown:
            print("unknown config keys: " + ", ".join(sorted(unknown)), file=sys.stderr)
            return 2
        p.update(cfg)
    for k in DEFAULTS:
        val = getattr(a, k)
        if val is not None:
            p[k] = val
    try:
        if a.json:
            print(json.dumps(compute(p), indent=2))
        else:
            print(report(p, a.target_margin))
    except ValueError as e:
        print("error: " + str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
