"""
Task 2: RAG Dataset Creation & Summarization

Builds a compact, structured customer_segments.json for Elite Builds LLC to
be embedded/retrieved by a RAG system. Numbers are pulled straight from
Task 1's derived signals (not re-typed by hand) so the segmentation always
stays consistent with the underlying transaction math. The output is kept
under 300 tokens per the assignment spec -- token count is estimated with
tiktoken when available, falling back to a conservative chars/4 heuristic.

Usage:
    python scripts/rag_segmentation.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from signal_engineering import build_signals, load_transactions  # noqa: E402

OUTPUT_PATH = ROOT / "output" / "customer_segments.json"
TOKEN_LIMIT = 300


def count_tokens(text: str) -> int:
    """Best-effort token count. Uses tiktoken (cl100k_base) if installed,
    otherwise falls back to the common ~4-chars-per-token approximation."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def build_customer_segments(signals: dict) -> dict:
    cash_flow = signals["cash_flow_summary"]
    resilience = next(s for s in signals["signals"] if s["name"] == "Resilience Alpha")
    vendor_changes = sorted(
        v["pct_change_first_to_latest_payment"]
        for v in resilience["evidence"]["vendor_payment_trend"].values()
    )
    reinvestment = next(s for s in signals["signals"] if s["name"] == "Growth Reinvestment")
    reinvestment_total = reinvestment["evidence"]["total_reinvestment"]
    reinvestment_pct = reinvestment["evidence"]["pct_of_revenue"]
    velocity = next(s for s in signals["signals"] if s["name"] == "Expense Velocity Discipline")
    velocity_pct = velocity["evidence"]["pct_change"]

    return {
        "customer_id": "ELITE_BUILDS_LLC",
        "industry": "Residential Construction",
        "region": "Utah, US",
        # Structured metrics kept separate from the narrative segments below
        # so a RAG consumer can pull exact numbers without parsing prose. No
        # margin "multiple" here: our cash-flow margin and the industry's
        # accrual net-margin benchmark are different accounting bases, so a
        # ratio between them isn't a valid comparison.
        "metrics": {
            "net_cash_flow_margin_pct": cash_flow["net_cash_flow_margin_pct"],
            "industry_avg_net_margin_pct": signals["market_context"]["industry_avg_net_margin_pct"],
            "reinvestment_pct_of_revenue": reinvestment_pct,
            "core_opex_pct_change_half_over_half": velocity_pct,
            "vendor_payment_pct_change_range": f"{vendor_changes[0]}% to {vendor_changes[-1]}%",
        },
        # Each field below covers exactly one idea, so a RAG retriever can
        # match a query (e.g. "vendor" or "savings") to a single field
        # instead of needing to parse a sentence combining several ideas.
        # Numbers already in `metrics` above aren't repeated here -- kept as
        # short as possible to hold down embedding/retrieval token cost.
        "segments": {
            "behavioral": {
                "vendor_payment_trend": "Vendor payments down; sector costs up 15%.",
                "opex_trend": "Core opex down half-over-half.",
                "reinvestment": f"${reinvestment_total:,}: tech, marketing, equipment capex.",
            },
            "demographics": {
                "business_type": "Small construction firm",
                "location": "Utah, USA",
                # Single month of data -- "observed credits", not a claimed recurring monthly rate.
                "revenue_band": f"${cash_flow['total_revenue']:,} observed credits",
            },
            "psychographics": {
                "brand_affinity": "AutoCAD indicates tech adoption.",
                "growth_orientation": "Equipment/marketing spend suggests growth focus.",
                # Exactly one Savings transaction exists in the data -- "regular"
                # would overclaim a recurring pattern that isn't there.
                "liquidity_posture": "Savings transfer observed.",
            },
        },
        "key_signal": (
            "Resilience Alpha: cash-flow margin well above industry benchmark "
            "despite sector's 15% material cost surge."
        ),
        "recommended_product": "Equipment Financing / Equipment Line of Credit",
    }


def main() -> None:
    transactions = load_transactions()
    signals = build_signals(transactions)
    segments = build_customer_segments(signals)

    serialized = json.dumps(segments, indent=2)
    token_count = count_tokens(json.dumps(segments))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(serialized)

    print(serialized)
    print(f"\nEstimated tokens: {token_count} (limit: {TOKEN_LIMIT})")
    print(f"Saved to {OUTPUT_PATH.relative_to(ROOT)}")

    if token_count > TOKEN_LIMIT:
        raise SystemExit(f"customer_segments.json exceeds the {TOKEN_LIMIT}-token limit")


if __name__ == "__main__":
    main()
