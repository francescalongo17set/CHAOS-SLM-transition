# 11 · Plan requirements

The next step after this handbook is one **implementation plan per pipeline**, plus one for the shared package. A plan is accepted only if it follows this chapter.

## Plans to produce

| Plan | Branch | Depends on |
|---|---|---|
| P0 · Shared package and data audit | `orchestrator/baselines` | Chapters 02–07 |
| P1 · Kev | `orchestrator/baselines-kev-0.8b` (then `-4b`, `-9b`) | P0 merged |
| P2 · Laya | `orchestrator/baselines-laya` | P0 merged |
| P3 · Nimble | `orchestrator/baselines-nimble` | P0 merged |
| P4 · Comparison | `orchestrator/baselines` | P1–P3 runs |

## Every plan must contain

1. **Goal and scope** in two sentences, quoting the decision IDs it relies on.
2. **Inputs**: files, splits, environment, secrets (names only).
3. **Open items**: every `PENDING` it touches (it must stop there, not decide) and every `PROPOSED` it adopts.
4. **Steps**, each with: purpose, exact files created or changed, command(s) to run, expected output, and a **check that can fail** (a test, a count, a validator).
5. **Time boxes** for steps that may not fit the free tier (for example the Nimble fit check).
6. **Failure handling**: what to log, what to report, when to stop. Never "retry until it works" against a quota.
7. **Outputs**: files and where they are committed.
8. **Definition of done**, copied from chapter 07 and adapted.

## Plan P0 (shared package) minimum steps

1. Data audit script and `audit_report.md` (chapter 02).
2. Data loader (reads `router.jsonl` and `manifest.json`; checksum the manifest).
3. State serializer (P-01) with golden tests.
4. Question config loader (`questions.en.yaml`, C-21).
5. Dispatcher plus the oracle unit test over all three splits (chapter 04).
6. Log writer and validator (chapter 06), including resume and flush behaviour.
7. Reference token counter (P-08).
8. Evaluation script and report generator (chapter 05), tested on a **synthetic log** (random predictions) and on a **perfect log** (gold labels, which must give 100% on every metric).
9. Cross-pipeline `comparison.md` generator that tolerates missing pipelines.

## Plans P1–P3 minimum steps

Follow the "Implementation steps" section of each pipeline chapter. Each plan adds a 5-row smoke test, a 50-row validation pilot, then full validation and test runs, then the shared report.

## Plan P4 (comparison)

Collect the three `metrics.json` files, produce `comparison.md`, flag non-comparable rows (different GPU or latency mode, hosted), list dropped pipelines with reasons, and state which model is the candidate for fine-tuning **only if the owner asks for a recommendation**. Do not recommend a winner on gaps within noise (chapter 05).

## Plan hygiene

- Plans are short. No plan restates chapters; it links to them.
- A plan that contradicts the decisions log is wrong. Update the log first (with the owner), then the plan.
- Each step that depends on a number from the internet (a version, a limit, a memory figure) re-checks it in the session and records the result in the run notes.
