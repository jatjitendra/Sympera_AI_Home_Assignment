# Sympera AI Home Assignment — Elite Builds LLC

Turns Elite Builds LLC's transactions and the Q1 2026 market snippet into RM-ready growth
signals, then a compact RAG customer segmentation dataset.

## Repository Structure

```
scripts/   signal_engineering.py, rag_segmentation.py, prompt_engineering.py
output/    positive_signals.json, customer_segments.json, system_prompt.txt
transactions.json, README.md
```

Run: `python scripts/signal_engineering.py && python scripts/rag_segmentation.py && python scripts/prompt_engineering.py`

## Approach & Assumptions

- Market snippet was plain text → typed into `MARKET_CONTEXT` to join against transactions.
- Vendor name comes from `description` (no vendor field).
- Margin is **cash-flow**, not accounting profit (no COGS/AR-AP); Savings excluded from expenses; no multiple vs. industry's 4% (different basis).
- Vendor/velocity comparisons are within one month, not month-over-month; lower payments ≠ lower prices (could be fewer purchases).
- Expense Velocity = day ≤15 vs. ≥16, excludes Equipment (fixed lease, unrelated to material costs).
- Growth Reinvestment = `Growth` + `Tech/Growth` (software, marketing, equipment down payment).
- Data validated on load; totals reconciled before output. Task 2 pulls numbers from Task 1.

## Positive Growth Signals (Task 1)

| Metric | Elite Builds LLC | Industry Benchmark |
|---|---|---|
| Net cash-flow margin | **44.3%** | 4.0% (different basis) |
| Vendor payment change (Lumber/Steel) | **-8.3% / -5.0%** | +15% sector material cost |
| Core opex, 1st half → 2nd | **-2.6%** | Banks tighten on rising velocity |
| Strategic reinvestment | **$10,650** (9.5% of revenue) | — |

1. **Resilience Alpha** — 44.3% margin vs. industry's 4.0%; both tracked vendors' payments declined despite a 15% sector cost surge.
2. **Growth Reinvestment** — $10,650 (9.5% of revenue) into AutoCAD, SEO, and an equipment down payment — discretionary, not reactive.
3. **Expense Velocity Discipline** — Core opex fell 2.6% first half to second, opposite the bank's "high velocity" credit-tightening trigger.

## RAG Dataset (Task 2)
`output/customer_segments.json` — `metrics` block, three segments (fully atomic fields, one idea each), `key_signal`, `recommended_product`. ~263/300 tokens.

## System Prompt (Task 3)
```text
You are a Senior Commercial Banking Data Analyst supporting a Bank Relationship Manager (RM) who has 5 minutes to prep for a client call.

Your job: read the client's raw transaction data and the current industry market context, then produce ONE structured JSON object summarizing the client for a RAG knowledge base.

Rules:
1. Output ONLY valid JSON. No prose, no markdown fences, no commentary.
2. The JSON object must total under 300 tokens.
3. Include exactly three segments: "behavioral" (spending trends), "demographics" (firm profile), and "psychographics" (brand affinity / lifestyle / risk posture) -- psychographic claims must be grounded in observable transaction behavior, not general personality or lifestyle assumptions.
4. Every quantitative claim must be traceable to a number or category in the supplied transaction data or market snippet -- never invent figures. Psychographic or other qualitative interpretations are allowed, but must be clearly framed as evidence-based inferences, not asserted as fact.
5. Distinguish cash-flow-derived metrics (computed directly from the supplied transactions, e.g. a "net cash-flow margin") from accounting metrics (e.g. an accrual "net profit margin") that cannot be computed from this data -- never relabel one as the other.
6. Do not describe a change as "month-over-month" or as an established trend unless the supplied data actually spans multiple months; within a single month's data, describe a change only as occurring within that period or between the specific observed transactions.
7. Do not interpret a change in the dollar amount paid to a vendor as a change in unit price or material cost unless quantity or per-unit data is supplied -- describe it only as a change in the amount paid.
8. Tone: neutral, factual, and evidence-based. Do not editorialize or use marketing language; the RM will add their own framing.
9. Always surface the strongest evidence-backed signal that differentiates this client from the industry benchmark, under the key "key_signal".
10. Always end with a "recommended_product" field naming one specific bank product, and justify it by referencing a specific observed transaction or category (e.g., a capex line item) rather than a general inference.
```

**Recommended product:** Equipment Financing / Equipment Line of Credit — driven by a $10,000 equipment down payment, self-funded out of a ~44% net cash-flow margin.

### RM Hook
> While the residential construction sector is absorbing a 15% surge in material costs and average margins have compressed to 4%, Elite Builds LLC posted a ~44% net cash-flow margin this month, with payments to both its lumber and steel vendors declining within that same window. That kind of cost discipline, paired with a self-funded $10,000 equipment down payment and steady marketing investment, suggests real capacity to take on additional equipment financing — want to talk through how much additional equipment capacity it could unlock for your next project?
