# Orchestrator Fine-tuning Handbook (round 2)

> **Status: DRAFT v0.1, 13 Nov 2026.** Guideline book for round 2 of the orchestrator work: fine-tuning **Laya-multilingual**, **Kev-0.8B** and **Kev-4B** on the Italian router dataset, then measuring each against its own zero-shot run from round 1 (the baselines handbook, `orchestrator/baselines/handbook/`). Shared data step and Kev-0.8B code done; Kev-0.8B run reported finished, files to be verified (see `plans/HANDOFF.md`). Laya and Kev-4B not started.  Written for teammates (read top to bottom) and coding agents (read the "Agent rules" first, then only the chapters named in your task).

## What this round is

Round 1 ran three decision models zero-shot. Round 2 trains three of them on `data-generation/data/final/train/router.jsonl` and scores them with the **unchanged round-1 harness**, so the change from zero-shot is a like-for-like measurement. Nimble was dropped in round 1 (baselines C-34); Kev-9B is not fine-tuned for now (too expensive, FT-C-02).

The three fine-tunings are **independent branches that can work in parallel**. They share one data step (chapter 02) that must be built and merged first.

Round-1 results to compare against (route accuracy / macro-F1, test): Laya 0.265 / 0.281 · Kev-0.8B 0.331 / 0.329 · Kev-4B 0.423 / 0.471. Validation: Laya 0.238 / 0.254 · Kev-0.8B 0.349 / 0.357 · Kev-4B 0.436 / 0.483. Kev-9B (0.567 / 0.617 on test) is reference only.

## Reading order

| # | File | Read it when |
|---|---|---|
| 01 | [Decisions log](01-decisions-log.md) | Always. Every decision, with its status. New log, IDs prefixed `FT-`. |
| 02 | [Training data and splits](02-training-data.md) | Before building any training file. Shared data step. |
| 03 | [Evaluation protocol](03-evaluation-protocol.md) | Before scoring anything. What stays identical to round 1, what is new. |
| 04 | [Repo, branches, environments](04-repo-branches-environments.md) | Setting up a branch or a Kaggle notebook. |
| 05 | [Pipeline: Laya](pipelines/laya.md) | Fine-tuning Laya-multilingual. |
| 06 | [Pipeline: Kev](pipelines/kev.md) | Fine-tuning Kev-0.8B or Kev-4B. |
| 07 | [Runner changes and tests](07-runner-changes-and-tests.md) | Changing the round-1 runners, writing the shared tests. |
| 08 | [Plan requirements](08-plan-requirements.md) | Generating an implementation plan from this book. |
| 09 | [Verify in session](09-verify-in-session.md) | Checks that must pass before a fact here is relied on. |
| 10 | [Sources and caveats](10-sources-and-caveats.md) | Where each fact comes from, what is unverified. |
| — | [Handoff](../plans/HANDOFF.md) | Always, after the README: current state, what to verify, what is left. |

The baselines handbook stays authoritative for everything not changed here (state template, questions, dispatcher, log schema, evaluation definitions). Read it first if you have not.

## Agent rules (non-negotiable)

1. **Stop and ask on ambiguity.** If a needed decision is `PENDING` in the [decisions log](01-decisions-log.md), or this book contradicts the code, the data or an upstream doc, do not choose. Write `BLOCKED: <one-line question>, <options you see>` and wait for the owner.
2. **Ground truth is `router.jsonl` only** (baselines C-03). Never edit, relabel, filter or "fix" rows. Report suspected label errors instead.
3. **Test is touched once per model**, after its configuration is frozen. Nothing is fitted or chosen on test. Validation is for stopping, epoch choice and at most one second configuration. The calibration partition is for the temperature only.
4. **Same state, questions, dispatcher and metrics as round 1** (chapter 03). Never retype question wording: build it through the baselines `QuestionConfig`.
5. **Never commit secrets** (tokens, keys) and never commit weights. Checkpoints go to a private Kaggle Dataset; the repo keeps only their sha256.
6. **Zero money.** Free tiers only, no exception (FT-C-08). If a step would cost money, stop and ask.
7. **Log every number you report.** Reported metrics must be reproducible from the prediction logs with the shared evaluation script.
8. **Record the environment** (GPU name, library versions, base and weights revision, sha256 of the checkpoint) in every run.
9. **Mark facts from the internet as unverified until you checked them yourself.** Chapter 09 lists what to check.
10. **Keep the docs in sync with every decision and change.** When the owner resolves a `PENDING` item, or a step changes a name, path, layout, schema or behaviour, update in the same piece of work: (a) the decisions log first (it wins over chapters), (b) every chapter and pipeline file that mentions the item (search for the old ID, name or path), (c) the status line of this README and the plan's status. Never leave a resolved item marked pending. Before finishing, search for the old wording and report what you updated.
11. **Reuse before writing.** The baselines package (`common/`, `kev/`, `laya/`, plans, notebooks) already solves data loading, serialization, question building, dispatching, logging and metrics. Import it; copy a pattern (for example the bundle builder) only when importing is impossible, and say so in the plan.

## Status tags

| Tag | Meaning | Agent behaviour |
|---|---|---|
| `CONFIRMED` | The owner said so. | Implement. |
| `DELEGATED` | The owner asked the handbook author to choose. | Implement; owner may override. |
| `PROPOSED` | A technical default chosen by the handbook author, not discussed with the owner. | Implement, but list it in your plan so it can be reviewed. |
| `PENDING` | Needs an owner decision. | **Stop and ask.** |
