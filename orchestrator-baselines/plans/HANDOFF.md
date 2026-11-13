# Handoff · where the baselines round stands

Updated 13 Nov 2026 (after merge of PR #3). Read the [handbook README](../handbook/README.md) rules first (stop and ask on `PENDING`, docs in sync). This file says what is done, where it lives, and what to do next.

## State

| Piece | Status | Where |
|---|---|---|
| P0 shared package + audit | **DONE**, on `orchestrator/baselines`, 43 tests pass | `common/`, `audit/`, [P0 plan](P0-shared-package.md) |
| P1 Kev-0.8B | **DONE and validated** (Kaggle T4, fp32, in-process). **Merged (PR #3).** | `orchestrator/baselines`: code in `kev/`, logs in `runs/kev/kev-0.8b-20261112-a/`, [P1 plan](P1-kev-0.8b.md) |
| Kev-4B | **DONE and validated** (Kaggle T4, bf16, C-32; `--dtype bf16` in `kev/run.py`, `kev/kaggle_kev_4b.ipynb`). **Merged (PR #5).** | branch `orchestrator/baselines-kev-4b`; logs `runs/kev/kev-4b-20261113-a/` |
| Kev-9B | **smoke PASSED on Kaggle 2 x T4 (owner, 13 Nov); full validation + test run IN PROGRESS (remote)**. `--shard` (`kev/shard.py`), `kev/kaggle_kev_9b.ipynb`, C-33. Logs not in the repo yet. | branch `orchestrator/baselines-kev-9b` (PR #5 with 4B is merged) |
| P2 Laya | **DONE**, merged (PR #4) | [P2 plan](P2-laya.md), `runs/laya/` |
| P3 Nimble | not started | [nimble.md](../handbook/pipelines/nimble.md); no plan written yet |
| P4 comparison | not started | `common/compare.py` exists and tolerates missing pipelines |

The docs in `handbook/` and `plans/P1-kev-0.8b.md` were brought over from the Kev branch so they are current here. The Kev code, notebook and run logs are now on this base too (PR #3).

## Kev-0.8B first results (test, 593 rows; one run, one wording, T4)

scope_check acc 0.788 · feature acc 0.663 · complexity acc 0.727 · needs_clarification acc 0.423 · **route acc 0.331 (macro-F1 0.329)** · refuse recall 0.126 (safety-leak slice 0.057) · ECE 0.27 on scope_check. Most wrong routes go wrong first at `needs_clarification` (191 of 397), then `scope_check` (126), then feature (80): Kev over-predicts `ambiguous`/`missing` for slots. Mean latency 431 ms (slow `causal_conv1d` fallback), 552 native input tokens, 3.2 GB peak GPU, 753M parameters. Full detail: `report_test.md` on the Kev branch. Do not rank models on small gaps (chapter 05).

## Kev-4B first results (test, 593 rows; one run, bf16, T4; run `kev-4b-20261113-a`)

scope_check acc 0.801 · feature acc 0.801 · complexity acc 0.822 · needs_clarification acc 0.383 · **route acc 0.423 (macro-F1 0.471)** · refuse recall 0.789 (safety-leak slice 0.771; prompt-injection 0.556 on 18 rows) · ECE 0.150 on scope_check. Still most wrong routes go wrong first at `needs_clarification` (183 of 397), then `scope_check` (118): clarification over-flagged (precision 0.233), `lightweight` recall 0.044. Mean latency 3640 ms (bf16 on a T4 without native bf16, plus the `causal_conv1d` fallback: **not comparable** with the 0.8B fp32 431 ms), 605 native input tokens, 8.9 GB peak GPU, 4.21B parameters. Adapter sha256 matches the model card. The dtype differs from the 0.8B run (C-32). Detail: `runs/kev/kev-4b-20261113-a/report_test.md`.

## How a pipeline run works (Kev, reuse the pattern)

1. `python kev/make_bundle.py` builds `dist/kev-bundle/` (code + data, 3.4 MB, git-ignored). Upload it as a **private** Kaggle Dataset; after any code change upload a new version. No git clone of this repo on Kaggle.
2. Notebook `kev/kaggle_kev_0.8b.ipynb`: attach the Dataset, GPU T4 x2, Internet on. Stages `smoke` (5 rows, asserts) → `validation` → `test` → report, stop at first failure. About 10 minutes in total. *Save Version → Save & Run All* keeps `/kaggle/working/runs/...`.
3. Download `runs/<pipeline>/<run_id>/`, validate with `common.logs.validate_log`, commit under `orchestrator-baselines/runs/` (the root `.gitignore` excepts it on the Kev branch; this branch's `.gitignore` needs the same exception line when runs are merged).

## Lessons that will save time

- Upstream names collide: `orchestrator-baselines/kev/` has no `__init__.py` and scripts add `common` with `sys.path.append`, so `import kev` is always upstream Kev. Keep it that way for Laya/Nimble.
- Heavy installs go in `/tmp` (own `uv` venv, Python 3.12+, kev's locked deps, `flash-linear-attention==0.5.2`). Kev needs the venv; `common/` needs only `pyyaml`, `tokenizers`, `huggingface_hub`, `pytest`.
- First request in a process is slow (kernel compile, about 100 s); the 10 warm-up rows absorb it (P-03).
- Hub **tags move**; pin commits and log `weights_sha256` (Kev: `9a45d25eb2ab761841196625383fa1dff0e56c1e`, chapter 12).
- Kaggle's P100 may lack kernels in this torch build (`sm_60`); the notebook's GPU check stops with a message. Use a T4.
- Adapter tests (`kev/tests`) skip on a machine without `pydantic` and upstream `kev`; they run in the notebook venv.
- A `run.py` fix (record adapter and base disk size) is untested on Kaggle; the 0.8B `run.json` was corrected by hand.

## What to do next

1. ~~Merge the Kev-0.8B branch~~ done (PR #3).
2. **Kev-9B, pick up here.** The owner started the full run (validation then test) of `kev/kaggle_kev_9b.ipynb` on Kaggle T4 x2 on 13 Nov; it was still running when this was written, and its results are unknown. The smoke stage passed, so the 2-GPU layer split loads and scores (the smoke logs were not shown to the agent: ask the owner for them, or look at `kev-9b-20261113-a-smoke/`). When the owner hands over the run folder `runs/kev/kev-9b-20261113-a/`:
   1. Put it under `orchestrator-baselines/runs/kev/` and validate both logs: `common.logs.validate_log(path, split)` (needs `pyyaml tokenizers huggingface_hub`; a throwaway venv works, `python -I`).
   2. Check `run.json`: `weights_sha256` must equal the model card's adapter sha256 `2b2a70cf4ef4440b6c22899e1f72c2f8ea5c6f65b19aa344539b4b8971d1f13d`; `dtype` bfloat16; `n_error_rows` 0; read `layer_split` and `peak_gpu_mem_mb_per_device` (new fields from `--shard`).
   3. Write the results section here (as for 4B), update the README status line, commit and push the branch, open a PR into `orchestrator/baselines` (same pattern as PR #3 and #5).
   4. Report honestly: the split loader is our own code (C-33), not covered by upstream tests, and 9B is bf16 like 4B (not the fp32 exact path); latency is in the fallback path and across two GPUs (cross-GPU copies), so it is **not comparable** with the 0.8B/4B latencies.
   If the run died, ask the owner for the error text and the per-GPU memory, report 9B as not run and where it broke (C-25), and do not retry with another approach (e.g. quantization) without asking: it would change the model.
3. **Nimble (P3)**: write the plan per [chapter 11](../handbook/11-plan-requirements.md) before code; it first needs X-05 (quantization) answered by the owner. Laya (P2) is done and merged (PR #4, see `P2-laya.md`).
4. **P4 comparison** when runs exist.

## Open items (owner)

- ~~Kev-4B dtype~~ decided: bf16 on T4 (C-32); the report must label the dtype mix with the 0.8B fp32 run.
- **`causal_conv1d`**: install it (needs compiling, may not work on the free tier) before any latency comparison between sizes, or label all Kev latencies as "fallback path". Default if unanswered: label.
- **X-04** (confidence definition) and **X-05** (quantization for Nimble): still `PENDING`, deferred by the owner.
- Not checked: Kev GitHub release checksums for the adapter (Hub hashes only, chapter 12).
