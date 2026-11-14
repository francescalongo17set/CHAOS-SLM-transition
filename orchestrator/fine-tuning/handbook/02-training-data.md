# 02 · Training data and splits (shared data step)

This chapter is the **shared step** every fine-tuning branch depends on. It lives on the base branch `orchestrator/ft` and is merged before the three pipeline branches start (chapter 04). Facts marked *(repo)* were computed on the train split on 13 Nov 2026 and must be re-checked by the audit step below.

> **v2 (FT-C-26, 14 Nov 2026):** data comes from `final_v2/`. The slot rules, the `date_reference` rule and the suspected-label-error paragraph below are v1 history and no longer apply: examples carry the three fixed questions only. Train facts below are the v2 ones.

## What must stay identical to round 1

| Item | Where | Rule |
|---|---|---|
| State text | `common.state.serialize_state` | Single-line JSON, keys `available_docs`, `history`, `request`, `ensure_ascii=False`. |
| Question text and option order | `common/questions.en.yaml` through `common.questions.QuestionConfig` | Never retype wording (baselines C-21, P-02). |
| Questions per row at evaluation | baselines runners | `scope_check`, `feature_classification`, `complexity_estimation`, nothing else (v2: no slot questions, baselines C-37). |
| Dispatcher | `common.dispatcher.dispatch` | `tau=None`. v2: `dispatch(scope_check, feature, complexity)`, 4 routes, no `needs_clarification`. |
| Logs and metrics | `common.logs`, `common.evaluate`, `common.report` | Unchanged. |

## Train split facts *(repo)*

2,092 rows. Routes (v2): lightweight 715, agentic 854, refuse 335, quick_reply 188 (the 356 v1 clarification rows moved to agentic or lightweight). Scope: in_scope 1,569, out_of_scope 335, quick_reply 188. Feature: none 523, product_policy_analysis 500, comparison 278, regulatory_consultation 273, client_drafting 259, ibip_screening 259. Complexity (only the 1,569 in_scope rows): simple 819, complex 750. `safety_leak` true on 126 rows. History length: 0 turns 1,288, 2 turns 696, 3 to 6 turns 108.

`labels` has `scope_check` and `feature` on every row; `complexity` and `missing_info` only on in_scope rows. `support.slot_status` maps slot to `present` / `missing` / `ambiguous` (4,292 / 240 / 116 over all rows). `missing_info` and `slot_status` stay in the rows as metadata and are **not trained on** in v2.

Groups: `support.bundle_id` has 805 groups (493 singletons, 185 of size 2, 110 of size 10, a few of 3 to 9). `support.pair_id` links 313 pairs of rows. `support.family` is **not** a usable group (the product families hold 251 to 337 rows each).

## Rules for building examples (implement exactly)

| Rule | Reason |
|---|---|
| Ask the complexity question only for rows that have `labels.complexity` (in_scope). Out-of-scope and quick_reply rows get no complexity label. | No gold exists; evaluation scores complexity on in_scope rows only. |
| *(v1 only, dropped in v2)* Slot questions: for each slot in `by_feature[gold feature]` that is **also a key of `support.slot_status`**, add one `slot:<n>` question labelled with that status. If the slot is not in `slot_status`, **skip that question**. This affects `insurer` on `product_policy_analysis` (51 train rows) and `comparison` (49 train rows), 100 train rows in total (baselines C-28: 140 across all splits). | No gold label exists; training on a guessed label would be noise. |
| `date_reference` is never asked (baselines C-29). 68 train regulatory rows carry it in `slot_status`; ignore it. | Matches evaluation. |
| Feature `none` has no slot questions (`by_feature.none = []`). | |
| Slot questions are built from the **gold** feature at train time (teacher forcing). At evaluation they come from the predicted feature; the cascade stays in the evaluation. | Baselines C-23. |

**Suspected label errors (FT-C-24).** 14 train rows (validation 4, test 2) have `date_reference` as their only non-present slot, so gold `expected_route` is `clarification` while no asked slot is missing. The flaw is in `expected_route`; the rows are not edited or dropped. Training targets are per-question labels and stay correct. The same rows can never be routed to clarification at evaluation (baselines C-29), which is part of the known cost there. Train ids: orc-000898, 001075, 001076, 001077, 001120, 001127, 001128, 001129, 001395, 001397, 001405, 001406, 001407, 001408.

Known train/eval asymmetry (not a bug): complexity is trained only on in_scope rows but asked on every row at evaluation and scored only on in_scope rows. The dispatcher returns `refuse` or `quick_reply` before it reads complexity, so the asymmetry cannot change a route.

## Internal example form

The builder `common/build_data.py` reads rows with `common.data.load_split("train")` and yields one `Example` per row:

```python
Example(query_id, state: str,                    # serialize_state(row.model_input)
        questions: list[Question],               # from QuestionConfig, in the order below
        labels: dict[qid, option_id])            # gold, one per question
```

Question ids and order per example (v2): `scope_check`, `feature_classification`, `complexity_estimation` (if labelled).

## The two file formats

### Kev JSONL (upstream `data-format.md`, `kev/data.py`)

One line per example. `state` **must be the serialized string**: a JSON object would be re-rendered as `key: value` lines and differ from evaluation, where the adapter passes `state=state_text`.

```json
{"state": "{\"available_docs\": [...], \"history\": [...], \"request\": \"...\"}",
 "questions": {
   "scope_check": {"type": "choice", "instructions": "...",
                   "criteria": {"in_scope": "...", "out_of_scope": "...", "quick_reply": "..."},
                   "label": "in_scope"},
   "slot:insurer": {"type": "choice", "instructions": "...",
                    "criteria": {"present": "...", "missing": "...", "ambiguous": "..."}, "label": "present"}}}
```

`criteria` and `instructions` are built exactly as `kev/adapter.py:build_request` does (`{id: text}` in canonical order; `q.instructions`).

Limits: a request is at most `MAX_PACKED` 2048 tokens, each question branch at most `MAX_BRANCH` 1024, the state at most `MAX_STATE` 384 (training default). Our states are at most 220 Qwen tokens; up to 7 questions per record must still fit 2048 packed tokens: check every record with `kev.model.fits(rec, tok)`, **zero drops allowed**. `load_records` does not check that labels match `criteria`; the builder asserts it. Partition files: `train.jsonl`, `calibration.jsonl`, `development.jsonl`.

### Laya JSONL (upstream `laya/train.py`)

One line per example, same questions, labels given as `expected` (hard label; `label_smoothing` stays 0.0):

```json
{"state": "<same string>",
 "questions": {"scope_check": {"type": "choice", "instructions": "...",
               "criteria": {"in_scope": "...", "...": "..."}}},
 "expected": {"scope_check": "in_scope", "feature_classification": "product_policy_analysis"}}
```

Upstream also accepts `gold[qid]["probabilities"]`; not needed with hard labels. Question construction is exactly `laya/laya_adapter.py:to_laya`. The upstream notebook stores `state`, `questions`, `gold` as JSON strings; whether `read_jsonl` / `read_data` accept our plain form is confirmed in the smoke test (chapter 09).

## Splits and no leakage (FT-C-07)

| Partition | Source | Use |
|---|---|---|
| train | train minus calibration (1,903 rows in v2) | fit weights |
| calibration | about 10% of train (about 210 rows), chosen by **group** (`bundle_id` and `pair_id` merged with union-find so no group straddles), stratified by `expected_route`, seed `20261113` | fit the temperature only |
| development | validation (298 rows) as is | stopping, epoch choice, choice between at most two configurations |
| test | test (593 rows) | one run per model after the configuration is frozen |

`common/checks.py` asserts, and the build fails otherwise: no `query_id` in two partitions; no `bundle_id` or `pair_id` in two partitions of train/calibration; zero test rows in any training file; counts equal the committed `data/manifest.json`; per-route counts in calibration within 20% of expected. The contamination filter against test already holds for train (the data card reports 13-gram and edit-ratio 0.90).

Laya's own `finetune()` splits calibration at random (`calib_frac` 0.1), which would leak bundle neighbours; it is therefore not used (chapter 05).

## Outputs of the shared step

```
orchestrator/fine-tuning/
  common/build_data.py  split.py  checks.py  tests/
  data/                 # generated, git-ignored; manifest.json (sha256 of every file) is committed
    kev/{train,calibration,development}.jsonl
    laya/{train,calibration,development}.jsonl
    manifest.json
```

## Audit step (first task)

Before building, re-compute the facts of this chapter on the real train file and report any difference (counts, slot rules, group sizes). A difference stops the step and goes to the owner.
