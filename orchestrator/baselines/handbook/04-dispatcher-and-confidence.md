# 04 · Dispatcher and confidence

> **v2 (13 Nov 2026, C-35 to C-37):** the orchestrator no longer decides missing information. Dataset v2 (`data-generation/data/final_v2/`) has 4 routes; the model answers 3 questions in one call per row. Round-1 (v1) text below is kept where it still describes the v1 runs in `../runs/`.

The dispatcher is **deterministic code**, not a model. It reads the orchestrator record and returns a route.

## Rule table (C-14)

Evaluated top to bottom; first match wins.

| Priority | Condition | Route |
|---|---|---|
| 1 | `scope_check == out_of_scope` | `refuse` |
| 2 | `scope_check == quick_reply` | `quick_reply` |
| 3 | `feature in {ibip_screening, client_drafting}` **or** `complexity == complex` | `agentic` |
| 4 | otherwise | `lightweight` |

v1 had a rule between 2 and 3: `needs_clarification` (any required slot `missing` or `ambiguous`) → `clarification`. It is removed in v2 (C-35): the agent gathers missing information. IBIP and client drafting always go to `agentic` because they are the sensitive features (C-14). The 94 v2 rows that were `clarification` in v1 but are simple and not sensitive are `lightweight` (C-36).

## Mandatory unit test (the dispatcher is not trusted until this passes)

For every row of train, validation and test, build the record from the **gold** labels (`scope_check`, `feature`, `complexity`; v2 does not use `slot_status`), run the dispatcher with the confidence override disabled, and compare with `support.expected_route`.

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
