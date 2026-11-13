# Plan FT-P2 · Kev-0.8B fine-tuning

Branch: `orchestrator/ft-kev-0.8b` (from `orchestrator/ft` once FT-P0 is merged, FT-C-17, FT-C-23). Run id `kev-0.8b-ft-a` (FT-P-03). Chapter 08 format; chapters 03, 04, 06 and 09 are linked, not restated.

Status: **code done; C0 and C1 passed on a Kaggle T4; the full run has NOT been run (earlier note saying it finished was wrong, corrected by the owner on 13 Nov 2026); next: c2 pilot and time projection** (see [HANDOFF](HANDOFF.md)). Earlier note, kept for history: code written, nothing run on a GPU. FT-P0 data step built (not committed): `data/kev/*.jsonl` and `data/manifest.json` generated, 8 data tests pass. Steps 2 to 4 written: `kev/train_kev.py`, `calibrate_kev.py`, `run_ft.py`, `make_bundle_ft.py`, `kaggle_kev_ft.ipynb`, 8 unit tests (16 tests pass locally, no GPU). Step 5 (C1) passed. Fix found there: checkpointing 1 for 0.8B (OOM at 0). Steps 6 to 10 (pilot, full run, calibration, evaluation, comparison) are to be verified from the run files.

**C0 findings from reading upstream `kev` at `2074cc4` (local clone, nothing executed):**
- `--data` records go through `load_records` then `materialize`, then `augment` every epoch (option order always shuffled; none/distractor options with the default probabilities): confirmed. Upstream's `load_records` accepts our three generated files, and a training record renders identically to the evaluation request built by `kev/adapter.py` (test `kev/tests/test_kev_format.py`).
- Records over the training context are **dropped with a printed message only**; `train_kev.py` therefore counts them before training and stops on any drop.
- `PointerHead` divides logits by `temperature` in eval mode only, so open item 2 holds: raw = `softmax(T * log p_calibrated)`; no second inference pass.
- `Checkpoint.warm_start` compares `base, base_revision, lora, head_dim, option_isolation, special_embeddings, weights` but **not `weights_dtype`**; `train_kev.py` compares it itself.
- The recipe (lr cap 5e-5, architecture from the meta, `--p_none_pair 0.25`) is `skills/kev-finetune/scripts/kev_modal.py` (`MAX_DELTA_LR`), not `modal_app.py`. Its calibration (`score` + `write_meta`, raw predictor, `fit_temperature(..., aggregation="micro")` on the calibration records) is what `calibrate_kev.py` mirrors, with the default 81-point grid (the released checkpoints used 121 points; recorded in `extra["temperature_fit"]`).
- Still to read in session: the contents of the released checkpoint's `meta.extra["args"]` (needs a download), peak memory and step time on a T4.

## 1. Goal and scope

Fine-tune Kev-0.8B (LoRA + pointer head, warm start from the released checkpoint) on the `train` partition and compare it with its own zero-shot run `kev-0.8b-20261112-a` on validation and test, through the unchanged round-1 harness. Relies on FT-C-01, 03, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 23 and FT-P-02, 03, 05, 06, 07, 08.

## 2. Inputs

- Data (from FT-P0, merged on `orchestrator/ft`): `data/kev/{train,calibration,development}.jsonl`, `data/manifest.json`; test and validation rows via `common.data.load_split`.
- Model: `jaredpalmer/kev-0.8b` at the pinned commit `9a45d25eb2ab761841196625383fa1dff0e56c1e` (the pin already used by the round-1 notebook; adapter and head hashes are identical to `bf75a6a8`, which is what Hub tag `v1.0` loaded in round 1). Upstream `kev` at `2074cc44256200bb37540103fa4572901faa10f3`, `flash-linear-attention==0.5.2`.
- Hardware: one Kaggle T4, free, fp32 (FT-C-08). Secrets (names only): `HF_TOKEN` if needed.
- Kaggle Dataset to attach: bundle from `kev/make_bundle_ft.py` (private).

## 3. What is reused, what is new

| Existing (imported or copied, baselines stays untouched) | Used for |
|---|---|
| `baselines/kev/adapter.py` (`KevScorer`, `build_request`, `probs_to_answer`) | Evaluation, imported as `orchestrator.baselines.kev.adapter`. Its `build_request` is also the reference for the training record format. |
| `baselines/kev/run.py` (loading, two-call scoring, `LogWriter`, `validate_log`, `run.json`) | Evaluation, **run as is** via `--model <checkpoint dir>`. |
| `baselines/kev/make_report.py`, `common/evaluate.py`, `report.py`, `logs.py`, `dispatcher.py`, `compare.py` | Reports and metrics, unchanged. |
| `baselines/kev/make_bundle.py` | Pattern copied into `make_bundle_ft.py` (its `OUT` and file list are hardcoded, so it cannot be imported). |
| `baselines/kev/kaggle_kev_0.8b.ipynb` | Cells 0 to 5 (config, `sh` helper, bundle discovery, venv with `uv`, `fla`, GPU sanity) copied; stages replaced. |

| New (under `orchestrator/fine-tuning/kev/`, no `__init__.py`) | Purpose |
|---|---|
| `train_kev.py` | Reads the released checkpoint's meta, builds the `kev.train` command (chapter 06), runs it, writes `train_report.json` and the training half of `run.json`. |
| `calibrate_kev.py` | Fits the temperature on `calibration.jsonl` and writes it into the checkpoint. |
| `run_ft.py` | Thin wrapper: runs `baselines/kev/run.py` unchanged, then adds the fine-tuning fields to `run.json` (see open item 1). `run.py` rewrites `run.json` on every call, so `train_kev.py` writes only `train_report.json` and `run_ft.py` merges it in after each split. |
| `make_bundle_ft.py`, `kaggle_kev_ft.ipynb` | Bundle and notebook (size is a parameter, `0.8b` first). |
| `tests/test_train_kev.py` | Command-building and meta handling on a fake meta; calibration on synthetic logits. No GPU. |

## 4. Open items

**PENDING touched:** none. FT-X-01 and FT-X-02 are not needed.

**PROPOSED adopted:** FT-P-02, 03, 05, 06, 07, 08.

**Questions raised by this plan (owner decides; the plan assumes the first option):**

1. **Where the `run.py` changes of chapter 07 go.** Chapter 04 says baselines is "imported, never edited" on these branches; chapter 07 says to change `kev/run.py`. Proposal: do not edit it. `run_ft.py` calls it unchanged and then patches `run.json` with `finetuned_from`, `train_run_id`, `weights_sha256` of adapter and `head.pt`, the fitted temperature, and the corrected `disk_mb_base` / `disk_mb`. Alternative: edit on this branch and say so.
2. **Raw and calibrated ECE (FT-C-15) without a second inference pass.** The head divides logits by `T` (confirmed in the source, see C0 findings), so the raw (T=1) distribution is `softmax(T * log p_calibrated)`: raw ECE is recomputed offline from the logs and the stored temperature, and nothing is re-scored. This also keeps "test once per model". The offline recomputation itself (shared `common` script) is not written yet; it needs the logged probabilities to carry enough precision, to be checked on the first validation log. Alternative: a second run with `KEV_TEMPERATURE=1.0` (about 7 min per split), but that is a second pass over test.
3. **Pinned revision:** `9a45d25e…` (above) rather than `bf75a6a8`. Same weights; `run.json` records both.

## 5. Steps

| # | Step | Files | Command | Check that can fail |
|---|---|---|---|---|
| 0 | **Wait for FT-P0.** Pull `orchestrator/ft` into the branch. | none | `git merge orchestrator/ft` | `data/manifest.json` present; `kev/*.jsonl` counts equal the manifest; `kev.model.fits` zero drops (FT-P0 step 3). |
| 1 | **C0 · read upstream** at `2074cc4`: `kev/train.py`, `kev/data.py`, `kev/checkpoint.py`, calibration scripts. Answer chapter 09 items 1 and 3, and open item 2 (where `temperature` enters the head). Read the released checkpoint meta (`kev.checkpoint.read_meta`) for `base`, `base_revision`, `lora`, `head_dim`, `option_isolation`, `special_embeddings`, `weights`, `extra["args"]`. | notes inside `runs/kev/kev-0.8b-ft-a/run.json` (`notes`) | notebook cell, no GPU needed | Every chapter 09 Kev answer written down; an unanswered one is `BLOCKED`. |
| 2 | **`train_kev.py`.** Builds the command of chapter 06 with the architecture arguments **taken from the meta, never defaults**; `--lr = min(meta lr, 5e-5)`, `--epochs 1`, `--batch 1 --accum 8`, `--p_none_pair 0.25`, `--seed 0`, `--dtype fp32 --weights_dtype fp32`, `--checkpointing 0`, no `--replay`. Prints the meta and the final command, writes `train_report.json` (args, meta, step times, peak memory, loss curve). | `kev/train_kev.py`, `kev/tests/test_train_kev.py` | `pytest orchestrator/fine-tuning/kev/tests` | Test: a fake meta produces the exact expected argument list; a mismatch between meta and an override raises. |
| 3 | **`calibrate_kev.py`.** Scores `calibration.jsonl` at `KEV_TEMPERATURE=1.0` with `kev.benchmark.evaluate_records` / `LocalPredictor`, fits `kev.metrics.fit_temperature(rows, aggregation="micro")`, writes it with `scripts/calibrate_checkpoint.py --temperature T --reason "fit on our calibration partition, n=..."`, records `temperature_fit` and `n` in `train_report.json`. | `kev/calibrate_kev.py` | notebook | Test on synthetic logits with a known temperature (recovers it within tolerance); the fitted T is finite and positive; argmax unchanged after writing. |
| 4 | **Bundle and notebook.** `make_bundle_ft.py` ships baselines `common`, `kev`, `audit`, `requirements-common.txt`, `pytest.ini`, `fine-tuning/{common,kev,data/kev,data/manifest.json}` and the three `final/*/router.jsonl` plus manifests. `kaggle_kev_ft.ipynb` stages stop at the first failure: `c0` → `c1` → `c2` → `c3` → `c4_validation` → `c4_test`. `c4_test` runs only if a `FROZEN = True` flag is set by hand after validation is reviewed (FT-C-14). | `kev/make_bundle_ft.py`, `kev/kaggle_kev_ft.ipynb` | `python kev/make_bundle_ft.py` | Bundle size printed; notebook JSON parses; one attached Dataset found (same assert as round 1). |
| 5 | **C1 · smoke** on Kaggle: 32 records, `--max_steps 1`, reload with `run_ft.py --model <dir> --smoke`. | run on Kaggle | notebook stage `c1` | Loss finite; checkpoint loads; `base_revision` equals the pin; smoke log passes `partial_validate`. |
| 6 | **C2 · pilot:** 300 records, 1 epoch; log step time and peak GPU memory; project the full run. If memory fails, rerun with `--checkpointing 1` once and note it. | `runs/kev/kev-0.8b-ft-a/train_report.json` | notebook stage `c2` | Projection for C2 + C3 (pilot, full epoch, calibration) is inside **2 h** (FT-C-13), else `BLOCKED`. If it is close, ask the owner to confirm the box (FT-C-13 note). |
| 7 | **C3 · full run** (1 epoch on about 1,880 records), then calibration (step 3). The development route macro-F1 is the validation evaluation of step 8 (development = validation, 298 rows): the notebook's `c4_validation` stage asserts it above 0.357 before test can be run. A second epoch only if development improves and the box allows it (otherwise a `-b` configuration needs the owner's go-ahead, FT-P-03). | checkpoint under `/kaggle/working/runs/kev-0.8b-ft-a/checkpoint` | notebook stage `c3` | Loss finite every step; **sanity check (FT-C-12): development route macro-F1 above 0.357**, else stop and report. |
| 8 | **C4 · evaluate.** Validation through `run_ft.py` (calibrated, fp32, in-process, same path as the zero-shot run), then `make_report.py`. After review and `FROZEN = True`, test once. Raw ECE per open item 2. | `runs/kev/kev-0.8b-ft-a/{validation,test}.jsonl`, `run.json`, `metrics_*.json`, `report_*.md` | notebook stages `c4_*` | `validate_log` clean; 0 error rows; dispatcher oracle 593/593; `run.json` has all fields of chapter 03 "Report layout". |
| 9 | **Checkpoint handling.** Upload adapter + `head.pt` as a private Kaggle Dataset (owner's account); record `adapter_sha256`, `head_sha256`, dataset name. Download `runs/`, validate, commit. | `run.json` | manual | Hashes in `run.json` equal the uploaded files; no weights in git. |
| 10 | **Comparison and docs sync.** Comparison table with paired-bootstrap intervals via the shared script (FT-P4); update decisions log, README status and this plan's status; grep old wording (rule 10). | handbook, this plan | `grep -rn` | Report of what was updated. |

## 6. Time boxes (FT-C-13)

C2 + C3 together: **2 h**. Projection method: pilot step time × (1,880 records ÷ records per step), plus calibration scoring of about 210 rows (about 1.5 min) and development scoring of 298 rows (about 2 min). Over the box, or a pilot that cannot run: stop, report, ask. C4 is separate. Re-check the Kaggle session length and weekly GPU quota in session (chapter 09 item 6) and note them in `run.json`.

## 7. Failure handling

Log and stop, never retry against the quota. `BLOCKED` triggers: records not accepted by `kev.train`, architecture mismatch on warm start, any record dropped by `kev.model.fits`, NaN loss, pilot projection beyond the box, failed sanity check, any failed chapter 09 item, a chapter 07 test that fails. A weak gain at 0.8B is a result, not a failure (chapter 06). No money (FT-C-08).

## 8. Outputs

Committed on `orchestrator/ft-kev-0.8b`: `kev/*` code and tests, `runs/kev/kev-0.8b-ft-a/` (logs after validation, `run.json`, `train_report.json`, reports), this plan. Not committed: weights (private Kaggle Dataset; sha256 in `run.json`), `data/` except `manifest.json`.

## 9. Definition of done

Chapter 04 list: smoke and pilot inside the box; full run, calibration, `train_report.json` and `run.json` complete; validation and test logs validated, oracle 593/593, 0 error rows; report and comparison with `kev-0.8b-20261112-a` with bootstrap intervals; docs synced; any `PENDING` or failed check listed in the pull request. After C0 and C1 are done, FT-P3 (Kev-4B) may start (FT-P-02).
