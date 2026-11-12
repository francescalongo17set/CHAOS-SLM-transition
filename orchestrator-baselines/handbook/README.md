# Orchestrator Baselines Handbook

> **Status: DRAFT v0.3, 12 Nov 2026** (decisions C-21 to C-29 added; shared package P0 built, see `../plans/P0-shared-package.md`; **Kev-0.8B run done on Kaggle T4, logs in `../runs/kev/`, see `../plans/P1-kev-0.8b.md`**; Kev-4B/9B, Laya, Nimble not started; only X-04 and X-05 still pending). Guideline book for the first experiment round of the orchestrator: three open decision models (**Kev**, **Laya**, **Nimble**) run **zero-shot** on the Italian router dataset. Written for two audiences: teammates (read top to bottom) and coding agents (read the "Agent rules" below first, then only the chapters named in your task).

## What this round is

The orchestrator reads one user request (plus conversation history and the list of available documents) and outputs a record: `scope_check`, `feature_classification`, `complexity_estimation`, `missing_info`, `confidence`. A deterministic **dispatcher** then turns the record into one of five routes (`lightweight`, `agentic`, `clarification`, `refuse`, `quick_reply`).

Round 1 answers one question: **how do three ready-made decision models behave on our data, with no training of our own?** The best performer is fine-tuned in a later round (out of scope here).

We compare them on: accuracy / per-class precision and recall / macro-F1, token consumption, model size, latency, and (as a by-product) the probability distributions needed to compute confidence later.

## Reading order

| # | File | Read it when |
|---|---|---|
| 01 | [Decisions log](01-decisions-log.md) | Always. Every decision, with its status. |
| 02 | [Data and task spec](02-data-and-task-spec.md) | Before touching `router.jsonl`. |
| 03 | [Decision schema](03-decision-schema.md) | Before writing any prompt or question set. |
| 04 | [Dispatcher and confidence](04-dispatcher-and-confidence.md) | Route rules, confidence, what is collected now vs later. |
| 05 | [Evaluation protocol](05-evaluation-protocol.md) | Metrics, latency, tokens, size, slices, report. |
| 06 | [Prediction log schema](06-prediction-log-schema.md) | Common output every pipeline must write. |
| 07 | [Repo, branches, environments](07-repo-branches-environments.md) | Setting up a branch / notebook. |
| 08 | [Pipeline: Kev](pipelines/kev.md) | Implementing the Kev pipeline. |
| 09 | [Pipeline: Laya](pipelines/laya.md) | Implementing the Laya pipeline. |
| 10 | [Pipeline: Nimble](pipelines/nimble.md) | Implementing the Nimble pipeline. |
| 11 | [Plan requirements](11-plan-requirements.md) | Generating an implementation plan from this book. |
| 12 | [Sources and caveats](12-sources-and-caveats.md) | Where each external fact comes from, what is unverified. |

## Agent rules (non-negotiable)

1. **Stop and ask on ambiguity.** If a needed decision is `PENDING` in the [decisions log](01-decisions-log.md), or the handbook contradicts the code, the data or an upstream doc, do not choose. Write `BLOCKED: <one-line question>, <options you see>` and wait for the owner.
2. **Ground truth is `router.jsonl` only.** Never edit, relabel, filter or "fix" rows. Report suspected label errors instead.
3. **No training, no tuning on test.** Round 1 is zero-shot. Nothing is fitted on any split in this round, including temperatures and thresholds.
4. **Same data, same questions, same metrics for all three pipelines.** Shared code lives in the shared package (chapter 07). A pipeline only implements what is specific to its model.
5. **Never commit secrets** (API keys, tokens). Read them from environment variables or Kaggle/Colab secrets.
6. **Zero money.** Free tiers only. If a step would cost money, stop and ask.
7. **Log every number you report.** Reported metrics must be reproducible from the prediction logs (chapter 06) with the shared evaluation script.
8. **Record the environment** (GPU name, library versions, model revision hash) in every run. Colab and Kaggle assign different GPUs on different days.
9. **Mark facts from the internet as unverified until you checked them yourself.** Several upstream docs contradict each other (see chapter 12).
10. **Keep the docs in sync with every decision and change.** When the owner resolves a `PENDING` item, or a step changes a name, path, layout, schema or behaviour, update in the same piece of work: (a) the [decisions log](01-decisions-log.md) first (it wins over chapters), (b) every chapter and pipeline file that mentions the item (search the handbook for the old ID, name or path), (c) the status line at the top of this README and the plan's status. Never leave a resolved item still marked pending, or a stale branch, file or option name. Before finishing, run a search for the old wording and report what you updated.

## Status tags used in this book

| Tag | Meaning | Agent behaviour |
|---|---|---|
| `CONFIRMED` | The owner said so. | Implement. |
| `DELEGATED` | The owner asked the handbook author to choose. | Implement; owner may override. |
| `PROPOSED` | A technical default chosen by the handbook author, not discussed with the owner. | Implement, but list it in your plan so it can be reviewed. |
| `PENDING` | Needs an owner decision. | **Stop and ask.** |
