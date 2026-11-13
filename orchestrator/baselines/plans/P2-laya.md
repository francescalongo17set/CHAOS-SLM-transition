# Plan P2 · Laya

Branch: `orchestrator/baselines-laya` (from `orchestrator/baselines`, P0 merged).
Status: **DONE** (13 Nov 2026): all steps run on a Kaggle T4; results in `runs/laya/laya-multilingual-a/` (test route accuracy 0.265, 0 errors, 0 truncated). Decisions C-30, C-31.

## 1. Goal and scope

Run `laya-multilingual` zero-shot on validation and test and produce the shared report, following chapter 09 step by step: smoke test, adapter, budget check, pilot, full runs, report (C-01, C-04, C-05, C-07, C-15, C-23, C-24, P-03, P-04). Only pipeline code is added; `common/` is not touched.

## 2. Inputs

- Data: `data-generation/data/final/{validation,test}/router.jsonl` through `common.data.load_split`.
- Shared package: `common/` as is.
- Model: `laya.load("convaiinnovations/laya", subfolder="multilingual")` (chapter 09, no `Router`).
- Library: `laya==0.4.31` (latest on PyPI on 13 Nov 2026).
- Hardware: Kaggle T4 (owner choice), one runtime for Laya only (C-26), `USE_TF=0`.
- Secrets (names only): `GITHUB_TOKEN` (Kaggle secret, read-only, to clone the private repo).

## 3. Open items

- **PENDING X-04:** not touched; the dispatcher runs with `tau=None`.
- **PROPOSED, adopted:** P-01 state, P-02 option order, P-03 batch 1 and 10 warm-up rows, P-04 validation + test, P-07 log schema, P-08 reference tokenizer, P-09 dtype (Laya's own default is used and recorded).
- **Owner answers (13 Nov 2026):** follow the handbook (smoke test, pilot, full runs); keep `laya/` without `__init__.py`; add a `.gitignore` exception for `orchestrator-baselines/runs/`; write this plan.
- **Assumptions:** section 9, approved by the owner (13 Nov 2026).

## 4. Steps

| # | Step (chapter 09) | Files | Command | Check that can fail |
|---|---|---|---|---|
| 0 | `.gitignore` exception so run logs can be committed (chapter 07). | root `.gitignore` (`!orchestrator-baselines/runs/`) | `git check-ignore orchestrator-baselines/runs/laya/x.jsonl` | Prints nothing. |
| 1 | **Smoke test.** Install, load the multilingual checkpoint, answer one question from the card on a short Italian string, print the whole result object. | `laya/laya_kaggle.ipynb` (first cells), `laya/requirements-laya.txt` | Kaggle cells | `answers[qid]["probabilities"]` exists and holds every option; the loaded checkpoint is `multilingual`. Otherwise stop and ask. |
| 2 | **Adapter.** Canonical question config → Laya `questions`; result → canonical `answers` with full distributions; uses `common.logs.build_record`. Unit test on 5 rows, one per route. | `laya/laya_adapter.py`, `laya/tests/test_laya_adapter.py` | `pytest laya/tests` | Each built line passes the shared validator's per-row checks. |
| 3 | **Budget check.** Count validation and test rows whose state exceeds the multilingual budget, with Laya's own tokenizer. | notebook cell | Kaggle cell | Count printed. More than a handful of rows → stop and ask (chapter 09). |
| 4 | **Pilot.** 50 validation rows; record latency, tokens, peak GPU memory, errors. | `laya/run_laya.py` (`--limit 50`), `runs/laya/<run_id>-pilot/` | Kaggle cell | Log has 50 lines; numbers written in `run.json` notes. |
| 5 | **Full runs** on validation and test. | `runs/laya/<run_id>/{validation,test}.jsonl`, `run.json` | `python laya/run_laya.py --run-id <id>` | `common.logs.validate_log` returns no errors. |
| 6 | **Report** with the shared script. | `runs/laya/<run_id>/report_<split>.md`, `metrics_<split>.json`, `confusion_*.csv` | `common.evaluate.evaluate` + `common.report.write_report` | Script runs on the validated logs. |

## 5. Time boxes

Download about 650-680 MB. About 900 rows × 2 calls; the card's T4 figure is tens of ms per call. If a full split has not finished in 1 hour, stop and report.

## 6. Failure handling

Logs are appended per row and resumable (`LogWriter`). A failed row is logged with `error` and counted wrong. Any stop-and-ask trigger of chapter 09 stops the run with a `BLOCKED:` line. No retries against a quota.

## 7. Outputs

Code in `orchestrator-baselines/laya/`. Results in `orchestrator-baselines/runs/laya/<run_id>/`, committed after the validator passes.

## 8. Definition of done (chapter 07)

1. Smoke test passed on 5 rows. 2. Pilot of 50 validation rows with latency, tokens, memory recorded. 3. Full validation and test runs complete, logs validated by the shared script. 4. `report.md` and `metrics.json` from the shared script. 5. `run.json` complete, notes on anything surprising. 6. Open questions in the PR description; X-04 not decided.

## 9. Assumptions (approved 13 Nov 2026)

1. **Two calls per row.** C-23 asks the slots of the *predicted* feature, which is only known after the first answer: call 1 asks scope, feature and complexity; call 2 asks that feature's slots (none for `none`). Latency and tokens are the sum of both calls (chapter 05).
2. **`input_tokens_native` = Laya's own `usage.input_tokens`**, summed over the two calls (chapter 05: tokens actually processed). `input_tokens_ref` = `common.tokens.RefTokenizer.count_ref` on the state plus every question asked.
3. **`temperature_applied: null`** per row (chapter 09). Laya applies the checkpoint's shipped temperatures inside `predict` but does not return the value; `run.json` notes say so.
4. **`run.json`** = the chapter 06 fields plus `max_len` and `head_max_len` (chapter 09 acceptance asks for them).
5. **Pins:** `laya==0.4.31` and the Hub revision of `convaiinnovations/laya` read at load time.
6. **5 rows for the unit test and smoke test:** the first validation row of each route (the audit does not list per-route ids, see section 10).
7. **The adapter unit test uses a stand-in agent** (no GPU, no download); the real model is checked in the smoke test.
8. **The pilot is its own run** (`<run_id>-pilot`). The shared validator rejects partial logs, so the pilot's numbers go in its `run.json` notes rather than a report.
9. **`pytest.ini` stays unchanged**; Laya tests run with `pytest laya/tests`.

## 10. Where the handbook does not match reality (reported, not edited)

1. **`.gitignore` vs chapter 07:** the root `.gitignore` ignores `runs/`, but run logs are meant to be committed (fixed by step 0).
2. **Layout vs library name (chapter 07, C-27):** a package `orchestrator-baselines/laya/` would hide the installed `laya` library. The folder is kept without `__init__.py` and with distinct module names.
3. **Distribution key (chapter 09, chapter 12):** the `laya` 0.4.31 source returns it as `answers[qid]["probabilities"]`; to be confirmed by the smoke test.
4. **Token accounting (chapter 09):** the chapter says all questions share one pass, so the state counts once. In the source each question is its own sequence that contains the state, so the state is processed once per question. Laya's `usage.input_tokens` reports the real total.
5. **Per-route row ids:** chapters 09 and 08 refer to "`query_id`s from the audit" for one row per route; `audit/audit_report.md` does not list them, and the P0 golden files do not exist in `common/tests/`.
6. **Disk size:** the card says about 647 MB; the `multilingual/` files on the Hub total 678 MB.
7. **README rule 10 (docs sync):** by owner instruction the handbook is not edited by the agent. Decisions are recorded in the log (C-30, C-31) and the README status line; the detail-level drift above is left in the chapters for the owner to decide.
