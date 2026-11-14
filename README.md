# CHAOS-SLM-transition

Small language models (SLMs) for an Italian insurance assistant. The repo covers three parts:

1. **Synthetic data**: Italian records built from three insurance PDFs.
2. **Orchestrator**: a model that reads a user request and decides how to handle it (the router).
3. **Answer writer**: a model that answers questions from retrieved policy text (QA).

Last updated: 14 Nov 2026.

## Repository layout

| Path | What it holds |
|---|---|
| [`data-generation/`](data-generation/) | Specs (`instructions/`) and the data build (`data/`): code, chunks, plan, final datasets, data card |
| [`orchestrator/baselines/`](orchestrator/baselines/) | Zero-shot baselines for the orchestrator: shared package, Kev and Laya pipelines, run logs and reports |
| [`orchestrator/fine-tuning/`](orchestrator/fine-tuning/) | Fine-tuning of the best baseline (Kev-0.8B): shared data step, training and calibration code, plans |
| [`question_answering_finetuning.ipynb`](question_answering_finetuning.ipynb) | Early notebook: prompting Qwen2.5-1.5B-Instruct for grounded QA over policy chunks |

## 1. Data (`data-generation/`)

- **Goal:** 4,500 synthetic Italian records: Dataset 1 (3,000 router examples) and Dataset 2 (1,500 question-answer examples), written by sub-agents from three insurance PDFs (Zurich Salute, Generali Immagina Adesso, Zurich Impresa). Zurich Impresa is kept for the test split only.
- **Spec:** `instructions/Guideline_book_v0.2_...md`. It wins over the older files in `instructions/`.
- **Status:** the build is finished (stages 0 to 10) with 4,473 of 4,500 records. All records are draft: `verified: false`.
- **Datasets:**
  - `data/final/` is v1: 5 routes (`lightweight`, `agentic`, `clarification`, `refuse`, `quick_reply`).
  - `data/final_v2/` is v2: 4 routes. The `clarification` route is gone and the agent gathers missing information itself. v2 is built from v1 by `data/code/make_v2.py`.

| v2 split | router | QA |
|---|---|---|
| train | 2,092 | 842 |
| validation | 298 | 150 |
| test | 593 | 493 |

- **Docs:** `data/HANDOFF.md` (full build history, read first), `data/final/data_card.md` (labels, risks, deviations), `data/quality_report.md`.
- **Not in git:** the source PDFs (`data/raw/`), extracted text and the embedding matrices. Put the PDFs back under `data/raw/` to rebuild.

## 2. Orchestrator baselines (`orchestrator/baselines/`)

The orchestrator reads one request, the conversation history and the available documents. It outputs `scope_check`, `feature_classification` and `complexity_estimation`, each with a confidence. A deterministic dispatcher turns these into a route.

Round 1 asks how ready-made decision models behave on our data with no training. v2 is the current setup: 4 routes and 3 questions answered in one call per row.

Test set, 593 rows, one run each (v2):

| | Kev-0.8B | Laya |
|---|---|---|
| route accuracy / macro-F1 | **0.654** / 0.550 | 0.415 / 0.421 |
| scope / feature / complexity accuracy | 0.788 / 0.663 / 0.727 | 0.649 / 0.337 / 0.523 |
| refuse recall | 0.126 | 0.411 |
| mean latency | 286 ms | 32.5 ms |

- The scope, feature and complexity labels are identical to v1. The route rise comes from dropping the weak clarification question, not from a better model. v1 and v2 route metrics are not comparable.
- Kev-4B and Kev-9B were run on v1 only (zero-shot). Nimble was dropped (decision C-34).
- Details: `runs/RUNS_REPORT_v2.md` and `runs/RUNS_REPORT.md`.
- Start from `plans/HANDOFF.md`, then `handbook/README.md`. The decisions log (`handbook/01-decisions-log.md`) is the source of truth.

## 3. Fine-tuning (`orchestrator/fine-tuning/`)

- Shared data step, Kev-0.8B training and calibration code, and the Kaggle notebook are written and tested locally.
- **No full fine-tuning run exists yet.** Only the smoke stages have run.
- The code and plans are still on dataset v1. Decide whether to rebuild the data step for v2 before running more.
- Laya and Kev-4B fine-tuning have not started.
- Start from `plans/HANDOFF.md`.

## Working rules

- Read the `HANDOFF.md` of the part you touch first. Where sections of a document disagree, the highest-numbered section wins.
- Stop and ask when a handbook item is marked `PENDING`. Keep the docs in sync with the code.
- Test data is used once per model. Zurich Impresa chunks stay in test only.
- Training runs on free Kaggle T4 GPUs. Run logs live in `runs/` and are tracked. Model weights, caches, `dist/` bundles and virtual environments are git-ignored.
- Each of `orchestrator/baselines/` and `orchestrator/fine-tuning/` has its own Python environment and tests (`pytest`).
