# Handoff · where the baselines round stands

Updated 13 Nov 2026. Read the [handbook README](../handbook/README.md) rules first (stop and ask on `PENDING`, docs in sync). This file says what is done, where it lives, and what to do next.

## State

| Piece | Status | Where |
|---|---|---|
| P0 shared package + audit | **DONE**, on `orchestrator/baselines`, 43 tests pass | `common/`, `audit/`, [P0 plan](P0-shared-package.md) |
| P1 Kev-0.8B | **DONE and validated** (Kaggle T4, fp32, in-process). **Not merged into this branch.** | branch `orchestrator/baselines-kev-0.8b` (pushed): code in `kev/`, logs in `runs/kev/kev-0.8b-20261112-a/`, [P1 plan](P1-kev-0.8b.md) |
| Kev-4B, Kev-9B | not started | would use `orchestrator/baselines-kev-4b` / `-9b` (C-27) |
| P2 Laya, P3 Nimble | not started | [laya.md](../handbook/pipelines/laya.md), [nimble.md](../handbook/pipelines/nimble.md); no plan written yet |
| P4 comparison | not started | `common/compare.py` exists and tolerates missing pipelines |

The docs in `handbook/` and `plans/P1-kev-0.8b.md` were brought over from the Kev branch so they are current here. The Kev code, notebook and run logs are only on the Kev branch.

## Kev-0.8B first results (test, 593 rows; one run, one wording, T4)

scope_check acc 0.788 · feature acc 0.663 · complexity acc 0.727 · needs_clarification acc 0.423 · **route acc 0.331 (macro-F1 0.329)** · refuse recall 0.126 (safety-leak slice 0.057) · ECE 0.27 on scope_check. Most wrong routes go wrong first at `needs_clarification` (191 of 397), then `scope_check` (126), then feature (80): Kev over-predicts `ambiguous`/`missing` for slots. Mean latency 431 ms (slow `causal_conv1d` fallback), 552 native input tokens, 3.2 GB peak GPU, 753M parameters. Full detail: `report_test.md` on the Kev branch. Do not rank models on small gaps (chapter 05).

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

1. **Merge `orchestrator/baselines-kev-0.8b` into `orchestrator/baselines`** (chapter 07 wants shared code on the base before the other pipelines start; Laya and Nimble will reuse `kev/make_bundle.py` and the notebook pattern). Expect a trivial conflict on the README status line and `.gitignore`: keep the Kev-branch versions. Needs the owner's OK; open a PR and put the open items below in its description.
2. **Kev-4B (and 9B)**: needs an owner decision first (below), then a new branch, a copy of the notebook with `MODEL=jaredpalmer/kev-4b@<commit>` (look up the commit and weights hash, tags move), and `--run-id kev-4b-...`.
3. **Laya (P2)** and **Nimble (P3)**: write each plan per [chapter 11](../handbook/11-plan-requirements.md) before code. Nimble first needs X-05 (quantization) answered.
4. **P4 comparison** when runs exist.

## Open items (owner)

- **Kev-4B dtype.** fp32 4B is about 16 GB and will not fit one T4; bf16 is about 8.4 GB but a T4 has no native bf16 (README says bf16 flips about 1 answer in 300). Options: bf16 on the T4, or another Kaggle GPU. Round 1 so far used fp32 for 0.8B; mixing dtypes across sizes must be stated in the report.
- **`causal_conv1d`**: install it (needs compiling, may not work on the free tier) before any latency comparison between sizes, or label all Kev latencies as "fallback path". Default if unanswered: label.
- **X-04** (confidence definition) and **X-05** (quantization for Nimble): still `PENDING`, deferred by the owner.
- Not checked: Kev GitHub release checksums for the adapter (Hub hashes only, chapter 12).
