# 01 · Decisions log (round 2, fine-tuning)

Single source of truth for round 2. If a chapter and this log disagree, this log wins and the chapter must be fixed. This is a **new log**: IDs are prefixed `FT-` so they do not clash with the baselines log (`C-xx`, `X-xx`), which stays authoritative for round 1 and for anything not changed here.

## Confirmed by the owner

| ID | Decision |
|---|---|
| FT-C-01 | Round 2 is **fine-tuning**. Questions, state template, dispatcher, logs and metrics stay identical to round 1, so each fine-tuned model is compared like for like with its own zero-shot run. |
| FT-C-02 | Models: **Laya-multilingual, Kev-0.8B, Kev-4B**. Kev-9B is **not** fine-tuned for now (too expensive). Nimble stays dropped (baselines C-34). |
| FT-C-03 | **Priority order: Laya, then Kev-0.8B, then Kev-4B** ("order matters"). The three runs are **independent branches that work in parallel**: a failed sanity check (FT-C-12) in one run stops that run and is reported, it does not block the others. |
| FT-C-04 | This handbook is a folder of chapters in the style of the baselines handbook, English. `IMPLEMENTATION.md` was only working notes; its content is split into these chapters and the file is deleted afterwards. Code and plans from round 1 are **reused**, not rewritten. |
| FT-C-05 | The upstream facts gathered for the technical spec (Kev trainer, Laya trainer) are **trusted as written** in these chapters. The "verify in session" list (chapter 09) still applies at run time. |
| FT-C-06 | Training data is `data-generation/data/final_v2/train/router.jsonl` (v1 `final/` until 14 Nov, see FT-C-26). `router.jsonl` stays the only ground truth (baselines C-03). |
| FT-C-07 | **Calibration split:** about 10% of train (about 210 rows), chosen by group (`bundle_id` and `pair_id` merged), stratified by `expected_route`, seed `20261113`. The validation split (298 rows) is the development set (stopping, epoch choice, per-epoch metrics). |
| FT-C-08 | **Zero money, Kaggle free tier.** No exception, so no paid Modal H100 run for Kev-4B. |
| FT-C-09 | Checkpoints are stored on **Kaggle** (private Dataset) for now. Training on the public information in the source PDFs is **allowed**. |
| FT-C-10 | Hyperparameters stay **as proposed** in chapters 05 and 06 ("keep the choices"). Shuffled option order during training (Kev's default augmentation) is **okay**. Class-imbalance levers (label smoothing, focal loss, Brier weight) are **off** in the first run. |
| FT-C-11 | Validation is **not** merged into training in this round. A train+validation refit belongs to the final phases. |
| FT-C-12 | **No success target** for now. Each run keeps a **sanity check**: if development route macro-F1 does not beat that model's own zero-shot value, the run stops and reports (v2 values: Laya 0.395, Kev-0.8B 0.596, Kev-4B not yet measured on v2; v1 values 0.254 / 0.357 / 0.483 are void). |
| FT-C-13 | **Time boxes:** Kev-4B 3 h, Kev-0.8B 2 h. *(Laya: the 2 h box was removed by the owner on 14 Nov 2026; the pilot still projects and records the run time, and the Kaggle session length and weekly quota still apply.)* The 0.8B value was given as "yes i guess 2 hrs": confirm it if the pilot projects anything close to the limit. |
| FT-C-14 | **Evaluation discipline:** validation first, then **test once per model** after the configuration is frozen. The comparison with zero-shot **shows paired-bootstrap 95% intervals on route accuracy** (same rows, fine-tuned minus zero-shot). There is **no decision rule** such as "interval must exclude zero" and no "scope and feature must not fall" clause. |
| FT-C-15 | **ECE is reported both raw (T=1) and calibrated, side by side.** |
| FT-C-16 | All round-1 axes carry over: quality metrics, per-route tables, refusal slices, tokens, latency, model size. Latency is comparable with zero-shot only on the same hardware and dtype. |
| FT-C-17 | **Branches:** base `orchestrator/ft` (shared data step and this handbook), then `orchestrator/ft-laya`, `orchestrator/ft-kev-0.8b`, `orchestrator/ft-kev-4b`. The shared step is merged into the base **before** the three branches start. |
| FT-C-18 | At least **two Kaggle accounts** are available. |
| FT-C-19 | Decision IDs in this log are prefixed `FT-`. |
| FT-C-20 | X-04 (confidence definition, τ) stays deferred. Logs keep full probability distributions, as in round 1. |
| FT-C-21 | Fine-tuning reports do **not** carry a "draft, unreviewed" label for the test set. |
| FT-C-22 | Coding agents stop and ask on ambiguity. |
| FT-C-23 | **Branch naming:** the existing branch `orchestrator/ft` is the base (13 Nov 2026); pipeline branches are `orchestrator/ft-laya`, `orchestrator/ft-kev-0.8b`, `orchestrator/ft-kev-4b`. Supersedes the `orchestrator/fine-tuning*` names in the first draft. The folder path `orchestrator/fine-tuning/` is unchanged. |
| FT-C-24 | *(void in v2: there is no clarification route, so these rows no longer differ.)* **`date_reference`-only rows are label errors in `expected_route`.** When the only non-present slot of a row is `date_reference` (never asked, baselines C-29), gold `clarification` is a flaw in the label, not in our data build. Such rows (train 14, validation 4, test 2) are **kept unchanged** (rule 2) and reported as suspected label errors: ids in `02-training-data.md`. Training is unaffected, since the trained targets are per-question labels, none of which is wrong; only `expected_route` is. Chapter 07 test 2 excluded exactly these rows. |
| FT-C-26 | (14 Nov 2026) **Fine-tuning moves to dataset v2** (owner: align `orchestrator/ft` with v2 after the v2 merge into `main`). Training, calibration and development data come from `final_v2/` (4 routes: lightweight, agentic, refuse, quick_reply). Examples have **3 questions at most** (scope, feature, complexity on in_scope rows); no slot questions, no `needs_clarification`. Follows baselines C-35 to C-37. `missing_info` and `slot_status` are not trained on. Supersedes the slot rules of chapter 02, FT-C-24 and the v1 sanity values of FT-C-12. The v1 smoke run `kev-0.8b-ft-a-c1` (trained on v1 with slot questions) is **stale**: do not compare against it or resume from it; a new run id is needed. |
| FT-C-25 | **Kev runs use the `causal_conv1d` kernel** (13 Nov, owner: "update the docs so in the future we use it"). Training, calibration and evaluation of fine-tuned Kev all run with the prebuilt wheel `causal_conv1d-1.7.0+cu12torch2.8cxx11abiTRUE-cp313-cp313-linux_x86_64.whl` (official release `v1.7.0`, installed by notebook `kev/kaggle_kev_ft.ipynb` cell 4, with a GPU check and automatic fallback; its sha256 is printed and recorded in `run.json` notes). Round-1 Kev inference used the slow fallback path, so **latency is no longer comparable with zero-shot Kev**; accuracy and macro-F1 comparisons stay valid but the kernel is numerically slightly different (note it in the report). If the wheel check fails the run continues on the fallback and `run.json` notes must say so. |

## Delegated (author's choice, owner may override)

None yet.

## Proposed technical defaults (listed in plans for review)

| ID | Proposal |
|---|---|
| FT-P-01 | **Account allocation:** the two accounts go first to Laya and Kev-0.8B (priority order, FT-C-03). Kev-4B starts when an account is free. |
| FT-P-02 | Kev-4B starts after Kev-0.8B has completed C0 and C1 (chapter 06), because the 0.8B answers the upstream-trainer questions once for every Kev size (chapter 09). |
| FT-P-03 | Run ids: `laya-ft-multilingual-a`, `kev-0.8b-ft-a`, `kev-4b-ft-a`; logs under `orchestrator/fine-tuning/runs/{laya,kev}/<run_id>/`. A second configuration, if used, takes suffix `-b`. |
| FT-P-04 | Paired bootstrap: resample test rows with replacement, 10,000 resamples, fixed seed; statistic = route accuracy of the fine-tuned run minus the zero-shot run on the same `query_id`s. Also reported for route macro-F1. |
| FT-P-05 | Training examples are built by one shared builder (chapter 02) and written in each trainer's own JSONL format; both formats are verified against the baselines question builders by tests (chapter 07). |
| FT-P-06 | Upload each checkpoint as a private Kaggle Dataset; the repo stores only `weights_sha256` and the path of the dataset. |
| FT-P-07 | Per-epoch checkpoints and per-epoch development metrics are kept for Laya; for Kev, evaluation at epoch end if the pilot shows it is cheap (chapter 06). |
| FT-P-08 | `--replay` and the public `decision-v7` suite are not used. If the suite is available in session, record it and ask. |

## Pending (agents must stop and ask)

| ID | Question | Why it matters |
|---|---|---|
| FT-X-01 | Should the baselines handbook and `HANDOFF.md` be edited to point to this round (plan table row, status, handoff state row)? The baselines "out of scope" list still says fine-tuning is out of scope for round 1, which stays true. | Keeps docs in sync (rule 10) but touches the baselines branch. |
| FT-X-02 | X-04: confidence statistic and low-confidence override scope. Deferred by the owner (FT-C-20). | Chapter 04 of the baselines handbook. Not needed for round 2. |

## Out of scope for round 2

Fine-tuning Kev-9B · paid compute · Nimble · τ tuning and the confidence override · cost analysis · the safety check itself · training on validation or test · class-imbalance levers in the first run · public release of checkpoints.
