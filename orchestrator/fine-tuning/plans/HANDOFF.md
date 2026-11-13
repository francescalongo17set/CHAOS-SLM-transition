# Handoff · where the fine-tuning round stands

Updated 13 Nov 2026. Read the [handbook README](../handbook/README.md) rules first (stop and ask on `PENDING`, docs in sync, test touched once per model). This file says what is done, where it lives, and what to do next. Branch: `orchestrator/ft` (FT-C-23).

## State

| Piece | Status | Where |
|---|---|---|
| FT-P0 shared data step | **DONE**, 9 tests pass locally, committed | `common/` (`audit_train.py`, `build_data.py`, `split.py`, `checks.py`, `tests/`), `data/manifest.json`. Audit matched chapter 02 exactly. |
| FT-P2 Kev-0.8B code | **DONE**, 8 unit tests + format-parity test pass locally | `kev/` (`train_kev.py`, `calibrate_kev.py`, `run_ft.py`, `make_bundle_ft.py`, `kaggle_kev_ft.ipynb`), [plan](FT-P2-kev-0.8b.md) |
| Kev-0.8B run `kev-0.8b-ft-a` | **NOT RUN YET (owner corrected, 13 Nov).** Only C0 and C1 (smoke) have run; the earlier note that the run was finished was wrong. No full training, calibration, validation or test exists. | will be `runs/kev/kev-0.8b-ft-a/`; today `runs/kev/` holds only the C1 scratch folders |
| FT-P1 Laya | not started; no code. Folders `laya/`, `data/laya/` exist; Laya JSONL is already generated | [chapter 05](../handbook/pipelines/laya.md) |
| FT-P3 Kev-4B | not started. Allowed now: C0 and C1 of 0.8B are done (FT-P-02) | [chapter 06](../handbook/pipelines/kev.md) |
| FT-P4 comparison | not started | `common/compare.py` in baselines; the shared bootstrap script (chapter 07 test 7) is not written |

## Verified on Kaggle (from the owner's notebook logs)

- T4 (sm_75, 15.6 GB), Python 3.13 venv, torch 2.8.0+cu128, transformers 5.17.0, fla 0.5.2, upstream `kev` at `2074cc4`.
- Released 0.8B meta: base `Qwen/Qwen3.5-0.8B-Base` at `dc7cdfe2…`, lora 16, head_dim 256, `option_isolation` false, `weights_dtype` fp32, temperature 2.351. Released args: lr 2e-5, batch 4, accum 2, checkpointing 1, dtype bf16 (autocast over fp32 weights), `lora_targets` all.
- **fp32 with `--checkpointing 0` ran out of memory** on the first forward (14.5 GB). 0.8B now defaults to checkpointing 1 (chapter 06 table updated).
- C1 smoke passed: warm start loaded 372 LoRA tensors + head, one step trained, `base_revision` equal to the released one, 5-row reload evaluation with 0 validator problems.
- **Changed 13 Nov (FT-C-25), not yet run:** notebook cell 4 now installs the prebuilt `causal_conv1d` v1.7.0 wheel (no compiler on Kaggle) with a GPU check and automatic fallback, and `STAGES` is `["c0", "c1", "c2"]` so the next session runs the pilot. The 1-step smoke took 301 s for 10 records (first step, fallback path), so the 2 h box (FT-C-13) is unconfirmed: read the c2 projection before c3 and stop and ask if it exceeds the box. The `runs/kev/` folder holds only the C1 scratch outputs, no real run yet.
- Not verified anywhere: `calibrate_kev.py`, the fine-tuned validation/test evaluation, `make_report.py` on a fine-tuned run. Check the first output of each.

## What the next agent does first (verify before relying on anything)

1. Look at `runs/kev/kev-0.8b-ft-a/`: `train_report.json`, `run.json`, `calibration/temperature.json`, `validation.jsonl`, `metrics_validation.json`, `report_validation.md`, and `test.jsonl` / `metrics_test.json` if test was run.
2. Validate every log: `common.logs.validate_log` clean, 0 error rows, dispatcher oracle 593/593 (chapter 03). `run.json` must hold: `finetuned_from`, `train_run_id`, `adapter_sha256`, `head_sha256`, `temperature_fit`, `training`. Missing or null: report, do not fill by hand.
3. Check the sanity check (FT-C-12): validation route macro-F1 above 0.357. If the notebook asserted it, say so; if not, compute it from `metrics_validation.json`.
4. Check that test was run **once** (FT-C-14) and after validation was reviewed. If it was run more than once or the configuration changed after validation, stop and ask the owner.
5. Fill the results table below from the files, never from memory. Then sync docs (rule 10).

## Results (fill from the files; empty means not yet verified)

| | Validation (route acc / macro-F1) | Test (route acc / macro-F1) | Zero-shot test | Temperature fitted | Train wall time |
|---|---|---|---|---|---|
| `kev-0.8b-ft-a` | | | 0.331 / 0.329 | | |

Also record: peak GPU memory in training, step time, records seen, the notebook stages that ran, Kaggle session length and weekly quota (chapter 09 item 6), the adapter and `head.pt` sha256 and the private Kaggle Dataset name that holds the checkpoint.

## Still to build

1. **Raw ECE (FT-C-15).** The head divides logits by `T`, so raw probabilities are `softmax(T * log p)` with `T = temperature_applied` from the log. A shared script computing raw and calibrated ECE side by side is not written; check first that the logged probabilities carry enough precision.
2. **Paired bootstrap and comparison table** (FT-P-04, chapter 03, test 7): `common/compare.py` style, not written. Report intervals, no decision rule (FT-C-14). Include the 14 / 4 / 2 `date_reference`-only rows note (FT-C-24): they can never route to clarification.
3. **Kev-4B** (FT-P3): copy `plans/FT-P2-kev-0.8b.md`. Open: resolve the short pin `139fdd94` to a full commit; `bf16` weights and `--dtype bf16`; checkpointing 1; the time box is 3 h and the 0.8B step time is the first indicator whether it fits (if the projection exceeds the box, stop and ask: FT-C-08, no paid run).
4. **Laya** (FT-P1): data is ready in `data/laya/`; the code is not written. Chapter 09 item 4 lists what to verify in `laya.train`.
5. **Docs left as drafts:** README status line, `plans/FT-P2-kev-0.8b.md` status line (update both once the run is verified).

## How a Kev run works (reuse)

1. `python orchestrator/fine-tuning/common/build_data.py` (writes `data/`, git-ignored except `manifest.json`), then `python orchestrator/fine-tuning/kev/make_bundle_ft.py` builds `dist/kev-ft-bundle/` (about 10.6 MB, git-ignored). Upload as a **new version** of the private Kaggle Dataset and **re-attach it in the notebook** (the notebook keeps the version it was attached with).
2. Notebook `kev/kaggle_kev_ft.ipynb`: one T4, Internet on, `SIZE` and `STAGES` in the config cell. Stages `c0` (meta, dry run) → `c1` smoke → `c2` pilot with time projection (asserts the box) → `c3` train + calibrate (resumable) → `c4_validation` (sanity assert) → `c4_test` (only with `FROZEN = True`, set by hand). Use *Save & Run All (Commit)* for long runs.
3. Download `runs/kev/<run_id>/`, validate, commit under `orchestrator/fine-tuning/runs/kev/` (the `.gitignore` exception exists). **Never commit weights**: upload the checkpoint folder to a private Kaggle Dataset and record the sha256.

## Lessons from this round

- `kev.train` refuses an existing `--out`; scratch stages clear their own folders, the full run needs a new run id.
- `warm_start` does not compare `weights_dtype`; `train_kev.py` does.
- A bundle that ships one format must verify the manifest with `prefix="kev/"`.
- Kaggle prints `No module named 'wrapt'` from `sitecustomize` on every Python start: harmless.
- Run folders keep the `-c1` / `-c2` suffix for scratch runs; they are not results and should not be committed.

## Open items (owner)

- FT-X-01 (edit the baselines handbook and HANDOFF to point to round 2) and FT-X-02 (X-04) remain `PENDING` / deferred.
- Confirm the 2 h time box for 0.8B if the pilot projected anything close to it (FT-C-13). Not checked here.
