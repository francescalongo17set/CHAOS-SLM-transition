# Plan FT-P1 · Laya (multilingual) fine-tuning

Branch: `orchestrator/ft-laya` (from `orchestrator/ft`, FT-C-17, FT-C-23). Run id `laya-ft-multilingual-a` (FT-P-03). Chapter 08 format; chapters 03, 04, 05 and 09 are linked, not restated.

Status: **DRAFT, 14 Nov 2026. No code written, nothing run.** Dataset v2 (FT-C-26): 3 questions per row, 4 routes. Data files already exist: `data/laya/{train 1,903, calibration 189, development 298}.jsonl` (git-ignored, rebuilt by `common/build_data.py`).

## 1. Goal and scope

Fine-tune `laya-multilingual` (whole model, RLCD loss) on the `train` partition and compare it with its own v2 zero-shot run `laya-v2-a` (validation route macro-F1 0.395, test 0.415 / 0.421), through the unchanged evaluation harness. Relies on FT-C-01, 03, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 23, 26 and FT-P-01, 03, 05, 06, 07.

## 2. Inputs

- Data: `data/laya/{train,calibration,development}.jsonl`, `data/manifest.json`; validation and test rows via `common.data.load_split`.
- Model: `convaiinnovations/laya`, subfolder `multilingual`, revision pinned from `HfApi().model_info(...).sha` (round 1: `85cc74dd`; record the full hash). `laya==0.4.31`, `USE_TF=0`.
- Hardware: one Kaggle T4, free, fp16 autocast, single process, no DDP (FT-C-08).
- Secrets (names only): `HF_TOKEN` if needed.
- Kaggle Dataset to attach: bundle from `laya/make_bundle_laya.py` (private; new).

## 3. What is reused, what is new

Correction to the earlier handoff note: `laya_adapter.py`, `run_laya.py` and the notebook live in **`orchestrator/baselines/laya/`**. `orchestrator/fine-tuning/laya/` is empty.

| Existing (imported, baselines untouched) | Used for |
|---|---|
| `baselines/laya/laya_adapter.py` (v2: one `predict` call, 3 questions) | Evaluation of the fine-tuned model, imported. |
| `baselines/laya/run_laya.py` | Pattern for `run_ft_laya.py`. It loads **from the Hub repo with a pinned revision and has no `--checkpoint` option**, so it cannot score a local fine-tuned folder as is (open item 1). |
| `baselines/common/*`, `baselines/kev/make_report.py` equivalents for Laya | Logs, metrics, reports, dispatcher, unchanged. |
| `baselines/laya/laya_kaggle.ipynb` | Cells for bundle discovery, install, GPU check, copied. |

| New (under `orchestrator/fine-tuning/laya/`, **no `__init__.py`**: a package named `laya` would hide the library) | Purpose |
|---|---|
| `train_laya.py` | Chapter 05 "Training script": load checkpoint, `items_from_rows`, `train_model` with per-epoch checkpoints and development scoring, calibration, `train_report.json`. |
| `run_ft_laya.py` | Evaluate a local checkpoint folder with the baselines adapter and logging, then add fine-tuning fields to `run.json`. |
| `make_bundle_laya.py`, `kaggle_laya_ft.ipynb` | Bundle and notebook, stages `b0` to `b4_test`. |
| `tests/test_train_laya.py` | Config building, skip handling, epoch selection, raw/calibrated probability handling on stand-ins. No GPU, no `laya` import. |

## 4. Open items

**PENDING touched:** none.

**PROPOSED adopted:** FT-P-03, 05, 06, 07.

**Decided (owner delegated the choice, 14 Nov 2026):**

1. **Evaluating a local checkpoint.** `baselines/laya/run_laya.py` cannot load a local folder. Decision: do not edit baselines. `run_ft_laya.py` re-implements only `load_agent` (`laya.load(<dir>)`, explicit checkpoint, fail if another is loaded) and reuses `run_split`, `LogWriter` and the adapter by import. Same approach as Kev (`run_ft.py`) and chapter 04.
2. **Raw and calibrated ECE (FT-C-15).** Decision: recompute raw offline, no second scoring pass, so "test once" (FT-C-14) holds. If Laya's temperature is a plain divisor of the logits, raw = `softmax(T * log p_calibrated)` with the per-question-type `T` stored in `train_report.json` and `run.json`. **B0 must confirm this** in `laya==0.4.31` (that the per-type scalar is what `predict()` applies, and that `temperature_by_options` is not applied in practice), and the first validation log must show probabilities with enough precision. **Fallback if either fails:** validation scored twice (raw: temperatures set to 1 in a copy of `rl_agent_config.json`; calibrated, about a minute each); test scored once, calibrated only, with ECE reported calibrated-only and stated as such. Ask before any raw pass on test.

3. **v2 sanity value** (noted, not a question). FT-C-12 uses the v2 zero-shot development route macro-F1 **0.395** (`laya-v2-a`, validation). The Laya v2 run was a single run; no noise estimate exists.
4. **`temperature_applied`** (noted, not a question). Round 1 logged `null` because Laya hides it. The fine-tuned run stores the fitted temperatures in `train_report.json` and `run.json` instead; the per-row log field stays `null`.

## 5. Steps

| # | Step | Files | Command | Check that can fail |
|---|---|---|---|---|
| 0 | **Data check.** `build_data.py` output equals `data/manifest.json`; counts 1,903 / 189 / 298; Laya records have `state`, `questions`, `expected` and only the 3 v2 questions. | none | `pytest orchestrator/fine-tuning/common/tests` | Manifest hashes match; no `slot:` key in any record. |
| 1 | **B0 · read upstream** at the installed `laya==0.4.31` (`laya/train.py`, `laya/common.py`). Answer chapter 09 item 4 and confirm the temperature form of open item 2 (accepts our JSONL, `train_model` and `on_epoch_end` signatures, `collate_items`, multilingual `max_len` / `head_max_len`, `laya.load(<dir>)` works on a saved folder). | notes in `train_report.json` | notebook cell, no GPU | Every chapter 09 Laya answer written down; an unanswered one is `BLOCKED`. |
| 2 | **`train_laya.py`** per chapter 05 steps 1 to 6. Config: 4 epochs, micro-batch 8 × accum 8, `encoder_lr` 2.5e-5, `head_lr` 1e-4, `min_lr` 1e-6, loss `rlcd`, `shuffle_options=()`, `label_smoothing` 0, seed 0, AMP on. `skipped` must be empty. Per-epoch checkpoint + development route macro-F1 in `epochs.jsonl`; best epoch kept. Then `calibration_records`, `fit_temperature_map`, `calibration_report`, `collapse_stats`. | `laya/train_laya.py`, `laya/tests/test_train_laya.py` | `pytest orchestrator/fine-tuning/laya/tests` | Tests: a skipped item stops the run; epoch selection picks the best development value; a collapsed question type stops the run; **the epoch callback restores `model.train()` after development scoring** (laya's `calibration_records` leaves the model in eval mode, B0 finding). Development route = argmax of logits + v2 dispatcher, not the `predict` path (same route, see `train_laya.py`). |
| 3 | **`run_ft_laya.py`.** Per open item 1. Fails if the loaded checkpoint is not the requested folder. Adds `finetuned_from`, `train_run_id`, `weights_sha256`, fitted temperatures, `epoch_selected` to `run.json`. | `laya/run_ft_laya.py` | notebook | Smoke log passes `partial_validate`; `run.json` has all chapter 03 fields. |
| 4 | **Bundle and notebook.** Bundle ships baselines `common`, `laya`, `requirements-common.txt`, `pytest.ini`, `fine-tuning/{common,laya,data/laya,data/manifest.json}` and the three `final_v2/*/router.jsonl` plus manifests. Stages stop at the first failure: `b0` → `b1` → `b2` → `b3` → `b4_validation` → `b4_test`; `b4_test` only with `FROZEN = True` set by hand (FT-C-14). | `laya/make_bundle_laya.py`, `laya/kaggle_laya_ft.ipynb` | `python laya/make_bundle_laya.py` | Bundle size printed; notebook JSON parses; one Dataset found; `check_manifest` passes on the attached copy. |
| 5 | **B1 · smoke** on Kaggle: 64 items, 1 epoch, save, reload with `laya.load(<dir>)`, predict one row. | run on Kaggle | notebook stage `b1` | Loss finite; reload works; config is multilingual (`max_len` 1024, `head_max_len` 256). |
| 6 | **B2 · pilot:** 1 epoch on all train, calibrate, score 50 validation rows. Record epoch time and peak memory; project B2 + B3. | `train_report.json` | notebook stage `b2` | No OOM; temperatures stored; projection recorded; `BLOCKED` only if it exceeds one Kaggle session or the weekly quota. |
| 7 | **B3 · full run** (4 epochs, per-epoch checkpoints). One second configuration allowed once, chosen on development, needs the `-b` suffix. | checkpoint folder (about 650 MB, not committed) | notebook stage `b3` | Loss finite; **sanity check (FT-C-12): best-epoch development route macro-F1 above 0.395**, else stop and report. |
| 8 | **B4 · evaluate.** Validation (calibrated; raw ECE recomputed offline per open item 2), report; after review and `FROZEN = True`, test once. | `runs/laya/laya-ft-multilingual-a/{validation,test}.jsonl`, `run.json`, `metrics_*.json`, `report_*.md` | notebook stages `b4_*` | `validate_log` clean; 0 error rows; dispatcher oracle 593/593; `truncated` count 0. |
| 9 | **Checkpoint handling.** Upload as a private Kaggle Dataset; record sha256 of `model.safetensors` and the Dataset name in `run.json`. | `run.json` | manual | Hash in `run.json` equals the uploaded file; no weights in git. |
| 10 | **Comparison and docs sync.** Table against `laya-v2-a` with paired-bootstrap intervals (FT-P4); update decisions log, README, HANDOFF; grep old wording (rule 10). | handbook, this plan | `grep -rn` | Report of what was updated. |

## 6. Time (FT-C-13 amended: no box for Laya, owner 14 Nov 2026)

No time limit for B2 + B3. Projection: pilot epoch time × 4 epochs, plus per-epoch development scoring (298 rows, about 1 min each), calibration scoring of 189 rows (514 question items; the per-bucket temperature map needs 2,000, so only per-type scalars) and model loads. The projection is recorded, not gated. If it exceeds one Kaggle session or the weekly quota, stop and ask. Re-check the Kaggle session length and weekly GPU quota in session (chapter 09 item 6) and note them in `run.json`.

## 7. Failure handling

Log and stop, never retry against the quota. `BLOCKED` triggers (chapter 05): any `skipped` item, collapse to a prior, failed sanity check, pilot projecting beyond one Kaggle session or the weekly quota, a need to change `head_max_len` or move to DDP, any failed chapter 09 item, a failing chapter 07 test. Note: there is no early stopping upstream, so a diverging run is caught by the per-epoch development scores. No money (FT-C-08).

## 8. Outputs

Committed on `orchestrator/ft-laya`: `laya/*` code and tests, `runs/laya/laya-ft-multilingual-a/` (logs after validation, `run.json`, `train_report.json`, `epochs.jsonl`, reports), this plan. Not committed: weights, `data/` except `manifest.json`.

## 9. Definition of done

Chapter 04 list: smoke and pilot done, projection recorded; full run, calibration, `train_report.json` and `run.json` complete; validation and test logs validated, oracle 593/593, 0 error rows, no truncation; report and comparison with `laya-v2-a` with bootstrap intervals; docs synced; any `PENDING` or failed check listed in the pull request.
