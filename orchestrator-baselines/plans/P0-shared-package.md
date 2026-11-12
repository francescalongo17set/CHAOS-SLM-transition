# Plan P0 · Shared package and data audit

Branch: `orchestrator/baselines` (no new branch; the pipeline branches start only after this is merged, chapter 07).
Status: DRAFT for owner review. Nothing has been implemented.

## 1. Goal and scope

Build the model-independent code every pipeline imports (data loader, state serializer, question config, dispatcher, log writer/validator, token counter, evaluation script, comparison generator) and audit the data before anything is built on it. Relies on C-02, C-03, C-06, C-07, C-08, C-14, C-15, L-01, L-02 and P-01, P-02, P-04, P-07, P-08 (chapters 02-07, 11).

## 2. Inputs

- `data-generation/data/final/{validation,test}/{router.jsonl,manifest.json}`. The train split is read by the audit only (counts) and is not run (chapter 05).
- Reference tokenizer: Qwen3.5 (P-08). The exact Hub id and file access are unverified; resolve in step 7. No secrets are needed unless the tokenizer repo is gated (env var `HF_TOKEN`, name only).
- Python 3.12 venv, laptop only. `common/` depends on the standard library, `pyyaml` and `tokenizers` (no torch, no transformers).

## 3. Open items

**Resolved by the owner (see decisions log C-21 to C-27):** question language is English with one wording, so `questions.en.yaml` is written for real in step 4. Slot questions are 3-way and asked for the predicted feature. The loader still supports the other form via config but only the 3-way form is used.

**Still PENDING:**
- **X-04** (confidence definition): deferred until after the runs. The dispatcher accepts `tau=None` only and raises on a non-None `tau`.
- **X-05** (quantization, Nimble only): not touched.

**PROPOSED, adopted (review these):**
- **P-01** state template, **P-02** fixed option order, **P-04** validation + test, **P-07** log schema, **P-08** Qwen3.5 reference tokenizer.
- **Layout (approved, C-27):** the handbook now lives at `orchestrator-baselines/handbook/`, so code goes in `orchestrator-baselines/{common,audit,kev,laya,nimble,runs,reports}/` instead of `experiments/baselines/`. Chapter 07 should be updated to match once approved.

## 4. Steps

Each step ends with a check that can fail. Tests use `pytest` in `orchestrator-baselines/common/tests/`.

| # | Step | Files | Check |
|---|---|---|---|
| 1 | **Data audit** (chapter 02, items 1-8). Standalone script, writes `audit_report.md`. Compares the real data with chapter 02 and lists every difference. | `audit/audit.py`, `audit/audit_report.md` | Row counts equal 2,092 / 298 / 593. Every chapter-02 claim reported as PASS or DIFF. **Any DIFF stops the plan (rule 1).** Item 6 (token lengths) is filled in after step 7. |
| 2 | **Data loader.** Reads `router.jsonl`, exposes the model-visible fields only (`history`, `query`, `available_docs`) separately from gold (`labels`, `support`). Verifies manifest sha256 and returns it for `run.json`. Read-only, never rewrites rows. | `common/data.py` | Test: loaded counts match the manifests. Test: the model-visible object contains no key from `labels`, `support`, `resolved_slots`, `selected_doc_id` (C-07). |
| 3 | **State serializer (P-01).** Fixed key order and spacing, `history` always present, `available_docs` verbatim, `request` is the query. | `common/state.py`, `common/tests/golden/` | Golden-file tests on 5 rows (one per route, ids from the audit). Test: output is byte-identical on a second call; empty history gives `"history": []`. |
| 4 | **Question config loader.** Schema for question id, type, option ids in canonical order, option text, optional per-language file. Rejects option ids that differ from chapter 03. Writes `questions.en.yaml` (C-21, C-22) with the chapter 03 wording. | `common/questions.py`, `common/questions.en.yaml` | Test: loader rejects a missing or reordered option. Hash of the file is exposed for `run.json`. |
| 5 | **Dispatcher + oracle test (chapter 04).** Rule table, `tau=None` only. Oracle: gold labels + `support.slot_status` -> route versus `support.expected_route`, over train, validation and test. | `common/dispatcher.py`, `common/tests/test_oracle.py` | **100% match on all three splits.** On any mismatch: stop, list `query_id`s with gold fields and expected route, ask the owner. Do not patch the rule table or the data. |
| 6 | **Log writer and validator (chapter 06).** Append one line and flush per request. Resume skips existing `query_id`s. Validator checks one line per `query_id` of the split (no gaps/duplicates), options complete, probabilities sum to 1 within 1e-3, slot keys complete, `latency_ms` present on non-error rows, errors counted as wrong. | `common/logs.py`, `common/tests/test_logs.py` | Tests: a killed-midway write resumes without duplicates. Validator rejects a gap, a duplicate, probs summing to 0.9, a missing option. |
| 7 | **Reference token counter (P-08, L-01).** Counts serialized state + question text once with the Qwen3.5 tokenizer. Resolve the tokenizer id and record it. Then fill audit item 6 (min/median/p95/max; counts over 512, 768, 1,024). | `common/tokens.py` | Test: same input, same count; counts are stable across runs. If the tokenizer cannot be fetched on the free tier, stop and ask (`BLOCKED`), do not substitute one. |
| 8 | **Evaluation script and report generator (chapter 05).** Reads a log plus `router.jsonl`. Masks, accuracy, per-class P/R/F1, macro-F1, confusion CSVs, needs_clarification, end-to-end route (`tau=None`), route attribution, refuse recall with safety-leak and `leak_type` slices, ECE (10 bins, per question) and Brier, token/latency/size tables (warm-up rows excluded from latency). Writes `report.md` and `metrics.json`. | `common/evaluate.py`, `common/report.py` | **Perfect log** (gold labels, probability 1.0) gives 100% on every metric and ECE 0. **Synthetic log** (seeded random) gives accuracy near chance, no crash, and a stable `metrics.json` hash. |
| 9 | **Comparison generator.** Side-by-side `comparison.md` from `metrics.json` files. Flags runs with a different GPU or latency mode, lists dropped pipelines with a reason. | `common/compare.py` | Test with 0, 1 and 3 pipelines present; missing pipelines are reported, not errors. |

## 5. Time boxes

No step needs a GPU. The only step that may exceed its box is the tokenizer download (step 7): 30 minutes, then stop and ask.

## 6. Failure handling

- A DIFF in the audit or an oracle mismatch -> stop at that step with the `query_id`s and the question for the owner. No fix to the rule table, the data or the book without the owner.
- Never edit `router.jsonl`. Suspected label errors go into `audit_report.md` under "suspected label errors" (rule 2).
- Anything fetched from the internet (tokenizer id, library versions) is recorded as unverified until checked in the session (rule 9).

## 7. Outputs (committed on `orchestrator/baselines`)

`orchestrator-baselines/common/`, `audit/audit_report.md`, golden test files, this plan. Large artefacts (tokenizer cache) are git-ignored. One commit per step; merge after the definition of done below.

## 8. Definition of done

1. Audit report complete, with zero unresolved DIFFs.
2. Oracle dispatcher test at 100% on all three splits.
3. Perfect-log and synthetic-log tests pass in `evaluate.py`.
4. Validator rejects every malformed-log case in step 6.
5. `common/` imports without torch or transformers (checked by importing it in a clean venv).
6. Chapter 07 updated for the new layout and decisions C-21 to C-27 reflected (X-04, X-05 still pending).
7. Open questions listed in the PR description.

## 9. After P0

Create `orchestrator/baselines-kev-0.8b` from the merged base (the `-0.8b` suffix is the owner's request; the 4B run would use `orchestrator/baselines-kev-4b`). Then write P1 (Kev); its former blockers are now resolved (C-21 to C-26).
