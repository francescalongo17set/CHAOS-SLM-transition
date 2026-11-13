# 08 · Plan requirements

The next step after this handbook is one **implementation plan per branch**. A plan is accepted only if it follows this chapter. Plans are short, link to chapters instead of restating them, and **reuse the round-1 plans, code and notebooks** (agent rule 11).

## Plans to produce

| Plan | Branch | Depends on | Reuses |
|---|---|---|---|
| FT-P0 · Shared data step | `orchestrator/ft` | baselines P0 (shared package) merged | `common.data`, `common.state`, `common.questions`, `common.dispatcher` |
| FT-P1 · Laya fine-tuning | `orchestrator/ft-laya` | FT-P0 merged | baselines P2 plan and `laya/run_laya.py` |
| FT-P2 · Kev-0.8B fine-tuning | `orchestrator/ft-kev-0.8b` | FT-P0 merged | baselines P1 plan, `kev/run.py`, `kev/make_bundle.py`, `kev/kaggle_kev_0.8b.ipynb` |
| FT-P3 · Kev-4B fine-tuning | `orchestrator/ft-kev-4b` | FT-P0 merged; FT-P2 steps C0 and C1 done (FT-P-02) | same as FT-P2 plus `--dtype bf16` handling |
| FT-P4 · Comparison | `orchestrator/ft` | FT-P1 to FT-P3 runs | `common/compare.py` |

FT-P1 and FT-P2 start first and run in parallel on the two accounts; FT-P3 starts when an account is free (FT-P-01).

## Every plan must contain

1. **Goal and scope** in two sentences, quoting the decision IDs it relies on.
2. **Inputs:** files, splits, environment, secrets (names only), the Kaggle Dataset to attach.
3. **Open items:** every `PENDING` it touches (it stops there) and every `PROPOSED` it adopts.
4. **Steps**, each with: purpose, exact files created or changed, command(s), expected output, and a **check that can fail** (a test, a count, a validator).
5. **Time boxes** from FT-C-13, with the projection method used in the pilot and what happens when it is exceeded (stop and ask).
6. **Failure handling:** what to log, what to report, when to stop. Never "retry until it works" against a quota.
7. **Outputs:** files and where they are committed; where the checkpoint goes (private Kaggle Dataset) and which hashes are recorded.
8. **Definition of done:** copied from chapter 04 and adapted.

## FT-P0 minimum steps

1. Re-compute the train facts of chapter 02 and report differences.
2. `build_data.py`: `Example` builder with the rules of chapter 02.
3. Kev and Laya JSONL writers; `kev.model.fits` check on every Kev record (zero drops).
4. `split.py`: group-disjoint calibration partition (union-find on `bundle_id` and `pair_id`, stratified by `expected_route`, seed `20261113`).
5. `checks.py`: the leakage assertions and counts versus `data/manifest.json`.
6. The seven tests of chapter 07.
7. Commit `data/manifest.json`; merge into `orchestrator/ft`.

## FT-P1 to FT-P3 minimum steps

Follow the "Steps and checks" tables of chapters 05 and 06, each with a smoke test, a pilot, the full run, calibration, the sanity check (FT-C-12), then evaluation on validation and test (chapter 03) and the report.

## FT-P4 (comparison)

Collect the `metrics.json` of each fine-tuned run and its zero-shot reference, produce the comparison with bootstrap intervals, flag non-comparable rows (hardware, dtype, path), list any run that stopped and why. State no winner on gaps within noise. Recommend a model **only if the owner asks**.

## Plan hygiene

- A plan that contradicts the decisions log is wrong: update the log first with the owner, then the plan.
- Each step that depends on a number from the internet (a version, a limit, a memory figure, a quota) re-checks it in session and records the result in the run notes (chapter 09).
- A failed sanity check, a projection beyond a time box, a skipped item or any `PENDING` is written as `BLOCKED: <question>, <options>` and the work stops.
