"""
Task 3: Prompt Engineering & RM Action Plan

This task is a prompt-design deliverable rather than a data-processing one:
it defines the exact system prompt used to turn Task 1's positive signals
into Task 2's customer_segments.json, plus the resulting bank product
recommendation and a ready-to-use RM 'Hook'. Kept as a runnable module (not
just markdown) so the prompt and its outputs stay one importable source of
truth; running it writes output/system_prompt.txt for easy inclusion in a
model-context/RAG pipeline.

Usage:
    python scripts/prompt_engineering.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "output" / "system_prompt.txt"

# The exact system prompt used to generate output/customer_segments.json.
# Persona: a bank data analyst writing FOR a Relationship Manager audience.
# Constraints handled: strict output format (JSON only), tone (neutral,
# evidence-based, no hype), and a hard token budget.
SYSTEM_PROMPT = """\
You are a Senior Commercial Banking Data Analyst supporting a Bank \
Relationship Manager (RM) who has 5 minutes to prep for a client call.

Your job: read the client's raw transaction data and the current industry \
market context, then produce ONE structured JSON object summarizing the \
client for a RAG knowledge base.

Rules:
1. Output ONLY valid JSON. No prose, no markdown fences, no commentary.
2. The JSON object must total under 300 tokens.
3. Include exactly three segments: "behavioral" (spending trends), \
"demographics" (firm profile), and "psychographics" (brand affinity / \
lifestyle / risk posture) -- psychographic claims must be grounded in \
observable transaction behavior, not general personality or lifestyle \
assumptions.
4. Every quantitative claim must be traceable to a number or category in \
the supplied transaction data or market snippet -- never invent figures. \
Psychographic or other qualitative interpretations are allowed, but must \
be clearly framed as evidence-based inferences, not asserted as fact.
5. Distinguish cash-flow-derived metrics (computed directly from the \
supplied transactions, e.g. a "net cash-flow margin") from accounting \
metrics (e.g. an accrual "net profit margin") that cannot be computed from \
this data -- never relabel one as the other.
6. Do not describe a change as "month-over-month" or as an established \
trend unless the supplied data actually spans multiple months; within a \
single month's data, describe a change only as occurring within that \
period or between the specific observed transactions.
7. Do not interpret a change in the dollar amount paid to a vendor as a \
change in unit price or material cost unless quantity or per-unit data is \
supplied -- describe it only as a change in the amount paid.
8. Tone: neutral, factual, and evidence-based. Do not editorialize or use \
marketing language; the RM will add their own framing.
9. Always surface the strongest evidence-backed signal that differentiates \
this client from the industry benchmark, under the key "key_signal".
10. Always end with a "recommended_product" field naming one specific bank \
product, and justify it by referencing a specific observed transaction or \
category (e.g., a capex line item) rather than a general inference.
"""

# The bank product recommendation, and why, in one line each.
PRODUCT_RECOMMENDATION = {
    "product": "Equipment Financing / Equipment Line of Credit",
    "rationale": (
        "The clearest single piece of evidence is a $10,000 equipment down payment this month, "
        "self-funded out of a ~44% net cash-flow margin -- equipment financing lets the client extend "
        "that same capex it has demonstrated it can self-fund, without drawing down the funds it moved "
        "to savings this same month."
    ),
}

# 2-sentence hook for the RM to open the conversation with.
RM_HOOK = (
    "While the residential construction sector is absorbing a 15% surge in material costs and average "
    "margins have compressed to 4%, Elite Builds LLC posted a ~44% net cash-flow margin this month, with "
    "payments to both its lumber and steel vendors declining within that same window. That kind of cost "
    "discipline, paired with a self-funded $10,000 equipment down payment and steady marketing "
    "investment, suggests real capacity to take on additional equipment financing -- want to talk "
    "through how much additional equipment capacity it could unlock for your next project?"
)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(SYSTEM_PROMPT, encoding="utf-8")

    print("=== SYSTEM PROMPT ===\n")
    print(SYSTEM_PROMPT)
    print("=== PRODUCT RECOMMENDATION ===\n")
    print(f"{PRODUCT_RECOMMENDATION['product']}\n{PRODUCT_RECOMMENDATION['rationale']}\n")
    print("=== RM HOOK ===\n")
    print(RM_HOOK)
    print(f"\nSaved system prompt to {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
