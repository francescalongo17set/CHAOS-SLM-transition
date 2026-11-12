# 04 · Dispatcher and confidence

The dispatcher is **deterministic code**, not a model. It reads the orchestrator record and returns a route.

## Rule table (C-14)

Evaluated top to bottom; first match wins.

| Priority | Condition | Route |
|---|---|---|
| 1 | `scope_check == out_of_scope` | `refuse` |
| 2 | `scope_check == quick_reply` | `quick_reply` |
| 3 | `needs_clarification` (any required slot `missing` or `ambiguous`) | `clarification` |
| 4 | `feature in {ibip_screening, client_drafting}` **or** `complexity == complex` | `agentic` |
| 5 | otherwise | `lightweight` |

Why clarification precedes agentic: in the sample, an IBIP or complex row with a missing slot has `expected_route = clarification`. Why IBIP and client drafting always go to agentic: they are the sensitive features (owner decision, C-14); in the sample a *simple* IBIP or drafting row has `expected_route = agentic`.

## Mandatory unit test (the dispatcher is not trusted until this passes)

For every row of train, validation and test, build the record from the **gold** labels and `support.slot_status`, run the dispatcher with the confidence override disabled, and compare with `support.expected_route`.

- 100% match → proceed.
- Any mismatch → **stop**, list the mismatching `query_id`s with gold fields and expected route, and ask the owner. The rule table or the data is wrong; do not patch either silently.

## Confidence override (C-15)

The owner's rule: **if the decision model's confidence is low, route to `agentic`.** The threshold τ will be tuned later. In round 1:

1. **Collect the full probability distribution** for every question of every row (chapter 06). This is mandatory.
2. Implement the dispatcher with an optional `tau` argument. `tau=None` disables the override. Round 1 headline numbers are reported with `tau=None`.
3. Do **not** tune τ and do not report τ-dependent results as findings. A threshold sweep is a later task.

Candidate confidence statistics, all computable offline from stored distributions (so nothing needs to be re-run):

| Name | Definition for a question with K options |
|---|---|
| `p_max` | highest probability |
| `margin` | highest minus second highest |
| `norm_conf` | `(p_max − 1/K) / (1 − 1/K)` (the formula used by Kev's API; for K=1, 1) |
| `entropy` | `−Σ p·log p`, optionally normalized by `log K` |

Open decisions (X-04, ask the owner before implementing the override):

- Which statistic is "the" confidence.
- How per-question confidences combine into a record-level confidence (for example minimum across the questions that decided the route).
- Whether the override applies to every output or only to some (for example should a low-confidence `refuse` or `quick_reply` go to agentic, or is that exempt?).
- Which splits τ is tuned on: validation only (the design in P-04 keeps test clean).

## What the confidence data must support later

- Risk-coverage per question: accuracy as a function of the confidence cut-off.
- Fraction of requests sent to agentic at each τ.
- Calibration (ECE, Brier) before and after any temperature fit, which needs the **raw** distribution. Each log row stores `temperature_applied` so it is clear what the stored probabilities are (chapter 06).
