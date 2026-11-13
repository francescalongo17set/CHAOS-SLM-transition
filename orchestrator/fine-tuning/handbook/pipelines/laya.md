# 05 · Pipeline: Laya (multilingual)

Branch: `orchestrator/fine-tuning-laya`. Run id `laya-ft-multilingual-a`. Priority 1 (FT-C-03). Read first: chapters 01 to 04. Facts marked *(upstream)* come from the Laya source read on 13 Nov 2026 (`laya` `main`, `laya.train`); nothing here has been run. Items in chapter 09 must be checked before they are relied on.

## Environment

`laya==0.4.31` (the round-1 version), `USE_TF=0`, Kaggle T4. Training uses fp16 autocast with `GradScaler` on CUDA (module default). `laya.train.finetune` is single-process; the upstream Kaggle 2×T4 notebook wraps it in `torchrun` and DDP. **First run on one T4, no DDP**; DDP only if the time box requires it (and then ask).

## Starting checkpoint

`laya.train.resolve_checkpoint_dir("multilingual")` resolves to `convaiinnovations/laya`, subfolder `multilingual` (downloads `rl_agent_config.json`, `model.safetensors`, `tokenizer/*`, `encoder/*`). The upstream notebook uses the English root checkpoint; our run passes `"multilingual"` (baselines C-05). `load_checkpoint` loads fp32 on CPU with `strict=True`. Pin the revision as round 1 did (`HfApi().model_info(...).sha`); the round-1 revision was `85cc74dd`.

## What trains *(upstream)*

The whole model (encoder at `encoder_lr`, decision head at `head_lr`) unless `freeze_encoder`. Loss `rlcd`: policy gradient over noisy logits with `rl_samples` 4, plus soft cross-entropy (`w_sph` 0.75, `w_rps` 1.0); noise `sigma` annealed from 0.4 to 0.1 across epochs. AdamW with two parameter groups, weight decay 0.01; `CosineAnnealingLR` to `min_lr` 1e-6, stepped per optimizer update; gradient clip 1.0. **There is no early stopping and no epoch selection upstream**: the final epoch is saved and `checkpoint_latest` is overwritten every epoch.

## Hyperparameters (FT-C-10: keep as proposed)

| Field | Value | Note |
|---|---|---|
| `epochs` | 4 | default and notebook |
| `micro_batch` × `grad_accum` | 8 × 8 on one GPU (64 per update) | the notebook uses 8 × 4 × 2 GPUs = 64 |
| `encoder_lr` / `head_lr` / `min_lr` | 2.5e-5 / 1e-4 / 1e-6 | defaults |
| `loss` | `rlcd` | default; `soft-ce` is the ablation if RLCD misbehaves |
| `max_len` / `head_max_len` | from the checkpoint (1024 / 256 for multilingual) | **do not change** `head_max_len` without asking (round-1 rule). State is truncated to `max_len`; option text shares the `head_max_len` budget. |
| `shuffle_options` | `()` (none) | canonical order (baselines P-02). Shuffling is a later ablation, not in the first run. |
| `label_smoothing` | 0.0 | FT-C-10 |
| `seed` | 0 | |
| `amp` | on (CUDA) | |

A second configuration (learning rate or epochs) is allowed **once**, chosen on development. Volume: about 1,880 rows give about 10,000 question items per epoch (3 core plus about 2.5 slot questions), about 160 updates per epoch, about 640 updates for 4 epochs. Upstream's "4 to 6 minutes" for its 6,000-decision notebook is an unmeasured estimate; the pilot measures ours.

## Training script: use the building blocks, not `finetune()`

`finetune()` does: load checkpoint, read data, `items_from_rows`, **random** `split_calibration`, evaluate base, `train_model`, `calibration_records`, `fit_temperature_map`, abstention thresholds, evaluate, write checkpoint. We need a group-disjoint calibration set (chapter 02) and per-epoch checkpoints, so `laya/train_laya.py` repeats those steps with the same functions:

1. `load_checkpoint(resolve_checkpoint_dir("multilingual"))`, tokenizer from the same folder.
2. `items_from_rows(tok, rows, max_len, head_max_len)` for the train, calibration and development files. **`skipped` must be empty** (reasons `options_collapsed`, `options_beyond_max_len`, `empty_*`, `invalid_*`); any skip stops the run and asks.
3. `train_model(model, tok, train_items, TrainConfig(...), device, max_len, head_max_len, on_epoch_end=cb)`. In `cb`: save an epoch checkpoint with `save_checkpoint`, append development metrics to `epochs.jsonl`. Route needs the dispatcher, so development is scored through the real `predict` path on the saved epoch folder (298 rows, about a minute). Keep the epoch with the best development route macro-F1.
4. For the chosen epoch: `calibration_records(model, tok, calibration_items, device, max_len, head_max_len)`, then `fit_temperature_map(records)`, giving `temperature` (per question type, minimum 10 records) and `temperature_by_options` (per bucket only with at least 2,000 records, so in practice only the per-type scalar applies). Store both in `rl_agent_config.json` through `save_checkpoint(model, tok, cfg, path)` (writes fp16 `model.safetensors`, `encoder/`, `tokenizer/`, config). Round 1 left Laya at the shipped temperatures; the fine-tuned model ships its fitted ones, logged as `temperature_applied`.
5. `calibration_report` and `collapse_stats` (upstream `prior_collapse_message`): if the model collapsed to a prior on some question type, stop and report.
6. Write `train_report.json`: config, skipped counts, per-epoch metrics, fitted temperatures, sha256 of `model.safetensors`, training peak GPU memory, epoch times.

**Raw versus calibrated ECE (FT-C-15).** The evaluation must be able to produce both. Plan the run so that a raw pass (temperatures set to 1) and a calibrated pass are both available: either evaluate twice (it is about a minute per split) or store logits. Decide in the plan and record it; ask if neither is possible with the runner.

## Steps and checks

| # | Step | Check that can fail |
|---|---|---|
| B0 | Read `laya/train.py` and `laya/common.py` at the installed version; answer the Laya items of chapter 09. | Notes in `train_report.json`. |
| B1 | Smoke: 64 items, 1 epoch, save, reload with `laya.load(<dir>)`, predict 1 row. | Loss finite; reload works; the config is the multilingual one (`max_len` 1024, `head_max_len` 256). |
| B2 | Pilot: 1 epoch on all train, calibrate, score 50 validation rows. | No OOM; epoch time recorded; temperatures stored. |
| B3 | Full run (4 epochs, per-epoch checkpoints). One second configuration allowed. | Sanity check (FT-C-12): best-epoch development route macro-F1 above the zero-shot **0.254**, else stop and report. |
| B4 | Evaluate (chapter 03): validation, then test once. | `validate_log` clean; 0 error rows; oracle 593/593; `truncated` count 0. |

**Time box (FT-C-13): 2 h on a Kaggle T4 for B2 and B3 together.** If the pilot projects more, stop and ask. The output folder (about 650 MB) is **not committed**: store its sha256 in `run.json` and upload it to a private Kaggle Dataset (FT-P-06).

## Round-1 behaviours to keep

- Explicit checkpoint, never the Router (round-1 rule): fail the run if a different checkpoint is loaded.
- Fixed canonical option order; no permutation averaging.
- Full probability distributions logged for every question.

## Acceptance criteria

- `train_report.json` and `run.json` complete; checkpoint sha256 recorded; Kaggle Dataset name recorded.
- Validation and test logs validated, oracle 593/593, no truncation.
- Comparison with `laya-multilingual-a` including bootstrap intervals (chapter 03).

## Stop-and-ask triggers

Any `skipped` item · collapse to a prior · sanity check failed · pilot projects beyond the 2 h box · a need to change `head_max_len` or move to DDP · any item of chapter 09 that fails.
