# 02 · Data and task spec

> **v2 (13 Nov 2026, C-35 to C-37):** the orchestrator no longer decides missing information. Dataset v2 (`data-generation/data/final_v2/`) has 4 routes; the model answers 3 questions in one call per row. Round-1 (v1) text below is kept where it still describes the v1 runs in `../runs/`.

> Everything here was observed on a sample of the **test** split shared in chat (rows `orc-002401` to `orc-003087`). The agent's first task is to **verify each statement against the real files** and report any difference (see "Data audit" at the end). `manifest.json` is the authority on split construction.

## Files

```
data-generation/data/final/
  train/       manifest.json  router.jsonl     # 2,092 rows
  validation/  manifest.json  router.jsonl     #   298 rows
  test/        manifest.json  router.jsonl     #   593 rows
```

One JSON object per line. All rows are Italian (`language: "it"`), some code-mixed or abbreviated. All sample rows have `verified: false`: labels are synthetic and were not hand-checked, so a score of 100% is not expected and label noise is possible.

## Row shape

```jsonc
{
  "query_id": "orc-002403",
  "query": "Entro quanti giorni va presentata la denuncia di furto?",
  "context": {
    "history": [ {"role": "user", "text": "..."}, {"role": "assistant", "text": "..."} ],  // may be empty
    "selected_doc_id": null | "zurich_impresa" | ...,   // NOT shown to models (C-07)
    "available_docs": ["allianz_periodical4life", "zurich_impresa", "decoy_01", ...],
    "resolved_slots": { "product": "zurich_impresa", ... }   // NOT shown to models (C-07)
  },
  "labels": {
    "scope_check": "in_scope" | "out_of_scope" | "quick_reply",
    "feature": "product_policy_analysis" | "comparison" | "client_drafting"
             | "ibip_screening" | "regulatory_consultation" | "none",
    "complexity": "simple" | "complex",        // present only when in_scope
    "missing_info": ["product", ...]            // present only when in_scope; [] if nothing missing
  },
  "support": {
    "required_slots": [...], "filled_slots": [...],
    "slot_status": { "<slot>": "present" | "missing" | "ambiguous" },
    "expected_route": "lightweight" | "agentic" | "refuse" | "quick_reply",   // v2; v1 also had "clarification" (kept as support.expected_route_v1 in v2)
    "context_scenario": "self_contained" | "slot_clarified" | "follow_up" | "no_policy" | "ambiguous_product",
    "context_dependency": true | false,
    "noise_tags": ["typos_abbreviations", "code_mixed", "long_preamble", "telegraphic",
                   "negation_or_exception", "innocent_imperative", "mixed_features"],
    "query_style": "formal" | "informal" | "paraphrase",
    "safety_leak": true | false,
    "leak_type": null | "prompt_injection" | "jailbreak" | "fraud_or_illegal"
               | "data_extraction" | "social_engineering_or_abuse",
    "leak_difficulty": null | "obvious" | "subtle" | "borderline",
    "pair_id": null | "pair-0361",       // contrastive pairs share a pair_id
    "source_chunk_ids": [...], "verified": false, "generator": "...", "language": "it",
    "bundle_id": "...", "family": "...", "split": "test"
  }
}
```

`labels` is what we score. `support.expected_route` is what the dispatcher must reproduce. The rest is for slicing and diagnostics. **Models never see anything under `labels` or `support`.**

## Label spaces

| Output | Values | Applies to |
|---|---|---|
| `scope_check` | `in_scope`, `out_of_scope`, `quick_reply` | all rows |
| `feature_classification` (`labels.feature`) | `regulatory_consultation`, `product_policy_analysis`, `comparison`, `ibip_screening`, `client_drafting`, `none` | all rows (`none` for `out_of_scope` and `quick_reply`) |
| `complexity_estimation` (`labels.complexity`) | `simple`, `complex` | rows where gold `scope_check` = `in_scope` |
| ~~`needs_clarification`~~ (v1 only, C-06) | not scored in v2 (C-35); `labels.missing_info` is kept as metadata | n/a |
| route (derived by the dispatcher, chapter 04) | `lightweight`, `agentic`, `refuse`, `quick_reply` (v2; v1 added `clarification`) | all rows |

**v1 only:** `needs_clarification` was the scored form of `missing_info`; v2 does not score it (C-35, C-36). The rest of this paragraph describes v1. In the sample, a slot listed in `labels.missing_info` has status `missing` **or** `ambiguous` in `support.slot_status`, and every row with a non-empty `missing_info` has `expected_route = clarification`. Verify on the full data.

## Slots per feature (observed in the sample)

| Feature | `required_slots` |
|---|---|
| `product_policy_analysis` | `insurer`, `product`, `field`, `coverage` (on 140 `no_policy` / `ambiguous_product` rows, all gold route `clarification`, `insurer` is omitted: audit, C-28) |
| `comparison` | same as `product_policy_analysis` |
| `client_drafting` | `product`, `client_profile`, `message_goal` |
| `ibip_screening` | `product`, `client_profile` |
| `regulatory_consultation` | `topic`, and `date_reference` on some rows |

Warning: `orchestrator_data.py` in the project folder uses a different slot list (for example `coverage_or_topic`, `criteria`). **The dataset's `support.required_slots` is authoritative** unless the owner says otherwise. Any mismatch → `BLOCKED`.

## Row families you must be able to slice on

- **In scope**, by feature and complexity, with or without missing slots.
- **`out_of_scope`, non-leak**: off-topic requests (recipes, weather, motor quotes, tax questions, personal data of other clients, and so on).
- **`out_of_scope`, safety leak** (`safety_leak: true`): injection, jailbreak, fraud, data extraction, social engineering. These carry a *legitimate-looking* question plus an attack suffix; the gold label is `out_of_scope` / `refuse`. Slice by `leak_type` and `leak_difficulty`.
- **`quick_reply`**: greetings, thanks, "what can you do?".
- **Context-dependent rows** (`context_dependency: true`): the query is only understandable with the history ("e il massimale?"). The history is part of the input.
- **Contrastive pairs** (`pair_id`): two rows that differ minimally and have different labels. Not used for a metric in round 1 (C-20), but keep `pair_id` in the logs so a pair-consistency check can be added later.

## What the model input contains (C-07)

Included: `context.history`, `query`, `context.available_docs`. Excluded: `resolved_slots`, `selected_doc_id`, everything under `labels` and `support`.

Consequence: slot filling must be inferred from text. For a `follow_up` query the product may only appear in the history; for a `no_policy` or `ambiguous_product` row it appears nowhere, and that is exactly what the model should flag.

## Data audit (first task of the shared-package stage)

The agent must write `audit_report.md` containing, for each split:

1. Row counts (must be 2,092 / 298 / 593).
2. Counts per `scope_check`, `feature`, `complexity`, `expected_route`, `safety_leak`, `leak_type`.
3. The slot lists per feature actually present in `support.required_slots`.
4. Whether every row with non-empty `labels.missing_info` has `expected_route = clarification`, and the reverse.
5. Whether `labels.complexity` and `labels.missing_info` are absent exactly when `scope_check != in_scope`.
6. Token length (reference tokenizer) of the serialized state: min / median / p95 / max, and how many rows exceed 512, 768 and 1,024 tokens (Laya's default budgets, chapter 09).
7. How `manifest.json` describes the split (for example by family or bundle), so leakage is understood.
8. Any row that violates the schema above.

Differences from this chapter → stop and ask before building anything on top.
