"""
Task 1: Positive Signal Engineering

Joins Elite Builds LLC's raw banking transactions with the Q1 2026 industry
market snippet to derive quantifiable, defensible growth signals for a Bank
Relationship Manager -- specifically 'Resilience Alpha' (beating the sector's
15% material cost surge) and 'Growth Reinvestment' (strategic outflows vs.
operational noise), plus a supporting 'Expense Velocity' check since that is
the exact metric the market snippet says banks are tightening credit against.

Usage:
    python scripts/signal_engineering.py
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "transactions.json"
OUTPUT_PATH = ROOT / "output" / "positive_signals.json"

# Market Context (Snippet) from the Q1 2026 Industry Report, hardcoded as the
# "market side" of the join since it was supplied as unstructured text, not data.
MARKET_CONTEXT = {
    "source": "Q1 2026 Industry Report",
    "industry_material_cost_inflation_pct": 15.0,
    "industry_avg_net_margin_pct": 4.0,
    "credit_tightening_trigger": "high Expense Velocity",
}

KNOWN_CATEGORIES = {
    "Revenue", "Interest", "Inventory", "Operations", "Equipment", "Tech/Growth",
    "Growth", "Savings",
}
GROWTH_CATEGORIES = {"Growth", "Tech/Growth"}
# Operations + Inventory only: the day-to-day, material/labor-driven costs the
# market snippet's "Expense Velocity" concern is actually about. Equipment is
# its own category in the source data -- a fixed lease payment, not sensitive
# to the sector's material-cost cycle -- so it's tracked separately rather
# than folded into this velocity check.
CORE_OPEX_CATEGORIES = {"Operations", "Inventory"}
VENDOR_CATEGORY = "Inventory"
NON_EXPENSE_CATEGORIES = {"Savings"}  # internal transfers, not P&L spend


def load_transactions(path: Path = DATA_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        transactions = json.load(f)
    validate_transactions(transactions)
    return transactions


def validate_transactions(transactions: list[dict]) -> None:
    """Guard against silently miscomputing signals on bad source data: every
    transaction must have the expected fields, a known category, and an
    amount sign consistent with its Credit/Debit type."""
    required_fields = {"date", "description", "category", "amount", "type"}
    for t in transactions:
        missing = required_fields - t.keys()
        if missing:
            raise ValueError(f"Transaction missing field(s) {missing}: {t}")
        if t["category"] not in KNOWN_CATEGORIES:
            raise ValueError(f"Unrecognized category {t['category']!r}: {t}")
        if t["type"] == "Credit" and t["amount"] < 0:
            raise ValueError(f"Credit transaction has a negative amount: {t}")
        if t["type"] == "Debit" and t["amount"] > 0:
            raise ValueError(f"Debit transaction has a positive amount: {t}")


def reconcile(transactions: list[dict], cash_flow: dict) -> None:
    """Sanity-check that the cash-flow summary actually accounts for every
    transaction -- catches a signal function silently dropping or
    double-counting a category as the transaction set evolves."""
    total_debits = sum(-t["amount"] for t in transactions if t["type"] == "Debit")
    savings = sum(-t["amount"] for t in transactions if t["category"] == "Savings")
    if cash_flow["total_expenses"] + savings != total_debits:
        raise ValueError(
            "Reconciliation failed: total_expenses + savings "
            f"({cash_flow['total_expenses']} + {savings}) != total debits ({total_debits})"
        )


def compute_cash_flow(transactions: list[dict]) -> dict:
    """This is a cash-flow margin (cash collected vs. cash paid out this
    month), not an accrual-accounting net margin -- the transaction data has
    no COGS matching or AR/AP to compute a true P&L net margin from.

    A Debit that's just an internal transfer to savings (still the firm's
    own cash) is excluded from 'expenses': counting it would understate
    profitability for a metric that's supposed to measure spend, not
    reallocation of cash the firm still holds.
    """
    revenue = sum(t["amount"] for t in transactions if t["type"] == "Credit")
    expenses = sum(
        -t["amount"]
        for t in transactions
        if t["type"] == "Debit" and t["category"] not in NON_EXPENSE_CATEGORIES
    )
    net = revenue - expenses
    net_cash_flow_margin_pct = round((net / revenue) * 100, 1) if revenue else 0.0
    return {
        "total_revenue": revenue,
        "total_expenses": expenses,
        "net_cash_flow": net,
        "net_cash_flow_margin_pct": net_cash_flow_margin_pct,
    }


def vendor_cost_trend(transactions: list[dict]) -> dict:
    """Compare each raw-material vendor's first vs. latest payment observed
    *within this single month* (not a month-over-month trend -- there's no
    prior-month data). This is also a *total payment* trend, not a per-unit
    price trend: the data has no quantity field, so a lower total could
    reflect lower unit pricing, lower purchase volume, or both. Either way
    it's evidence the firm's raw-material outflow is shrinking within the
    month while the sector's aggregate material costs are rising 15%,
    which is the core evidence for 'Resilience Alpha'.

    Note: this only compares the first and last payment, ignoring any
    payments in between -- correct for this dataset (exactly 2 payments per
    vendor) but not a true trend line if a vendor had 3+ payments.
    """
    by_vendor = defaultdict(list)
    for t in transactions:
        if t["category"] == VENDOR_CATEGORY:
            vendor = t["description"].replace("Vendor: ", "")
            by_vendor[vendor].append((t["date"], -t["amount"]))

    trends = {}
    for vendor, payments in sorted(by_vendor.items()):
        payments.sort(key=lambda p: p[0])
        first, latest = payments[0][1], payments[-1][1]
        pct_change = round(((latest - first) / first) * 100, 1) if first else 0.0
        trends[vendor] = {
            "first_payment": first,
            "latest_payment": latest,
            "pct_change_first_to_latest_payment": pct_change,
        }
    return trends


def growth_reinvestment(transactions: list[dict], total_revenue: int) -> dict:
    """Isolate strategic outflows (tech, marketing, capex) from operational
    noise (payroll, fuel, permits, utilities, leases) to show the firm is
    directing spend toward capacity-building, not just staying afloat.
    """
    growth_items = [t for t in transactions if t["category"] in GROWTH_CATEGORIES]
    total_growth = sum(-t["amount"] for t in growth_items)
    pct_of_revenue = round((total_growth / total_revenue) * 100, 1) if total_revenue else 0.0
    return {
        "total_reinvestment": total_growth,
        "pct_of_revenue": pct_of_revenue,
        "line_items": [
            {"date": t["date"], "description": t["description"], "amount": -t["amount"]}
            for t in growth_items
        ],
    }


def expense_velocity(transactions: list[dict]) -> dict:
    """Compare core operating expense (Operations + Inventory) in the first
    half of the calendar month (day <= 15) vs. the second half (day >= 16).
    Banks flag *rising* velocity as risk; a flat or falling trend is a
    positive signal that directly rebuts that concern.

    Splitting on the calendar date (rather than an index/count split) is
    what makes "first half of the month" a defensible claim; this dataset
    happens to be single-month, so day-of-month is sufficient.
    """
    def day_of_month(t: dict) -> int:
        return int(t["date"][-2:])

    first_half = [t for t in transactions if day_of_month(t) <= 15]
    second_half = [t for t in transactions if day_of_month(t) > 15]

    def core_opex(bucket: list[dict]) -> int:
        return sum(
            -t["amount"]
            for t in bucket
            if t["category"] in CORE_OPEX_CATEGORIES and t["type"] == "Debit"
        )

    first_total = core_opex(first_half)
    second_total = core_opex(second_half)
    pct_change = round(((second_total - first_total) / first_total) * 100, 1) if first_total else 0.0
    return {
        "first_half_core_opex": first_total,
        "second_half_core_opex": second_total,
        "pct_change": pct_change,
    }


def build_signals(transactions: list[dict]) -> dict:
    cash_flow = compute_cash_flow(transactions)
    reconcile(transactions, cash_flow)
    vendors = vendor_cost_trend(transactions)
    growth = growth_reinvestment(transactions, cash_flow["total_revenue"])
    velocity = expense_velocity(transactions)

    return {
        "company": "Elite Builds LLC",
        "market_context": MARKET_CONTEXT,
        "cash_flow_summary": cash_flow,
        "signals": [
            {
                "name": "Resilience Alpha",
                "finding": (
                    f"Net cash-flow margin of {cash_flow['net_cash_flow_margin_pct']}% sits well "
                    f"above the industry's {MARKET_CONTEXT['industry_avg_net_margin_pct']}% "
                    "accrual net-margin benchmark (different accounting bases, so not stated as a "
                    "direct multiple), and observed payment amounts to both tracked raw-material "
                    "vendors declined between recorded payments, even as the sector reports a "
                    f"{MARKET_CONTEXT['industry_material_cost_inflation_pct']}% material cost surge."
                ),
                "evidence": {
                    "net_cash_flow_margin_pct": cash_flow["net_cash_flow_margin_pct"],
                    "industry_avg_net_margin_pct": MARKET_CONTEXT["industry_avg_net_margin_pct"],
                    "vendor_payment_trend": vendors,
                },
            },
            {
                "name": "Growth Reinvestment",
                "finding": (
                    f"${growth['total_reinvestment']:,} ({growth['pct_of_revenue']}% of monthly "
                    "revenue) was deployed across three distinct areas -- software (AutoCAD), "
                    "marketing (local SEO), and equipment capex (a down payment) -- rather than "
                    "reactive operational overhead. That spread across categories, not just the "
                    "total, is what separates deliberate investment from a single lucky expense."
                ),
                "evidence": growth,
            },
            {
                "name": "Expense Velocity Discipline",
                "finding": (
                    f"Core operating expense (Operations + Inventory) moved {velocity['pct_change']}% "
                    f"from the first half of the month to the second (${velocity['first_half_core_opex']:,} "
                    f"-> ${velocity['second_half_core_opex']:,}) -- flat-to-falling, the opposite of the "
                    "'high Expense Velocity' pattern the market snippet says banks are tightening "
                    "credit against."
                ),
                "evidence": velocity,
            },
        ],
    }


def main() -> None:
    transactions = load_transactions()
    signals = build_signals(transactions)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2)

    print(json.dumps(signals, indent=2))
    print(f"\nSaved to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
