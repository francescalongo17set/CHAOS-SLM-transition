# 01 · Decisions log

Single source of truth for what is decided. If a chapter and this log disagree, this log wins and the chapter must be fixed.

## Confirmed by the owner

| ID | Decision |
|---|---|
| C-01 | Round 1 is **zero-shot only**. The best-performing model is fine-tuned in a later round. |
| C-02 | Data is in the repo at `./data-generation/data/final/{train,validation,test}/`. Each split folder holds `manifest.json` and `router.jsonl`. Sizes: train 2,092 · validation 298 · test 593. |
| C-03 | `router.jsonl` is the **only ground truth**, for evaluation now and fine-tuning later. |
| C-04 | Exactly three models: Kev, Laya, Nimble. No S1 (generation) or S2 (own readout) baselines. |
| C-05 | Kev: start with **Kev-0.8B**, then escalate to larger sizes. Laya: **`laya-multilingual`**. |
| C-06 | All outputs are scored against ground truth. `missing_info` is scored at the level **"needs clarification: yes/no"**. |
| C-07 | The model input is **conversation history + query + `available_docs`**. It does **not** see `resolved_slots` or `selected_doc_id`. |
| C-08 | Safety-leak rows (prompt injection, jailbreak, fraud, data extraction, social engineering) stay in the evaluation set on purpose: they reproduce the misses of the teammate's safety checker. They are labelled `out_of_scope` / route `refuse`. |
| C-09 | Metrics: accuracy, per-class precision and recall, macro-F1, and "all the necessary" others, kept lean. Plus token consumption, model size, latency. |
| C-10 | Latency is measured **per request, from the moment the request is sent to the moment the whole response is received**. |
| C-11 | Model size is reported. |
| C-12 | Hardware: **Kaggle and Colab free tiers only. Zero money.** |
| C-13 | Hosted APIs are allowed for Nimble. Sending the synthetic data to a hosted API is fine. If the hosted API is not free, try a local setup on Colab/Kaggle; if it does not fit, **drop Nimble and report it as dropped for hardware limits.** |
| C-14 | The route is decided by a **deterministic dispatcher** (chapter 04). IBIP screening and client drafting are sensitive and always go to the agentic path. The rule table in chapter 04 matches the owner's intent. |
| C-15 | **Low confidence → agentic.** The confidence threshold τ is tuned later. This round must **collect the full probability distribution for every output** so confidence can be computed afterwards. τ tuning itself is out of scope now. |
| C-16 | Git: base branch is `orchestrator/baselines`; the three pipelines are developed on separate branches started from it. |
| C-17 | The handbook is in English and is a folder. |
| C-18 | Coding agents stop and ask on ambiguity. |
| C-19 | No deadline is set for this round. |
| C-20 | No extra metrics "just in case". Keep the report lean. |
| C-21 | (was X-01) Question and option text in **English, one wording**. The data stays Italian. |
| C-22 | (was X-02a) Slot questions are **3-way** `present` / `missing` / `ambiguous`. |
| C-23 | (was X-02b) Slot questions are asked for the slots of the **predicted** feature (errors cascade). |
| C-24 | (was X-03) Latency for local models is measured with an **in-process library call**. Hosted runs stay marked not comparable. |
| C-25 | (was X-06) Kev: run **all sizes that fit** (0.8B, then 4B, then 9B). |
| C-26 | (was X-07) **One Python environment per pipeline** is acceptable. |
| C-27 | Branches carry the Kev size: `orchestrator/baselines-kev-0.8b`, and `-4b` / `-9b` for larger runs. Code lives in `orchestrator-baselines/{common,audit,kev,laya,nimble,runs,reports}/`. Tokenizer plan in P0 approved. |
| C-28 | Audit finding accepted (P0 step 1). `insurer` is absent from `required_slots` on 140 `product_policy_analysis` / `comparison` rows (`no_policy`, `ambiguous_product`; all gold route `clarification`). Slot questions ask all four slots for these features; only `needs_clarification` is scored (C-06); slot-level metrics, if ever added, skip `insurer` where gold lacks it. Chapter 02 amended. |
| C-29 | (was P-12) Only `topic` is asked for `regulatory_consultation`; `date_reference` is not asked (gold requires it on only 97 of 389 regulatory rows). Known cost: about 20 gold `date_reference` clarification cases go undetected. |
| C-32 | Kev-4B runs in **bf16 on a Kaggle T4** (13 Nov). fp32 (about 16 GB) does not fit one T4. Weights pinned to the model card's revision `139fdd94f1b6a6ad80cc15e08fcb99cac885a101` (Hub `main` has moved on to `6cfce5c2`). The report must state that 4B (bf16) and 0.8B (fp32) differ in dtype; per the Kev README bf16 flips about 1 answer in 300, so compare sizes with that caveat. |

## Delegated (author's choice, owner may override)

| ID | Decision |
|---|---|
| L-01 | **Tokens.** Report two numbers per request: `input_tokens_native` (tokens the model actually processed, counted with its own tokenizer, summed over all forward passes) and `input_tokens_ref` (the serialized state plus question text counted once with one shared reference tokenizer, so the three models are comparable). Output tokens are logged but not compared (none of the models generate text). |
| L-02 | **Kept extras.** (a) Recall on `refuse`, with a separate slice for safety-leak rows. (b) Per-route breakdown of the end-to-end route. (c) ECE and Brier score on the probabilities exactly as each model ships them (no refit). |
| L-03 | **Nimble version.** `Bespoke-Nimble-9B-v3` (LoRA adapter on Qwen3.5-9B) for the local fit check. Hosted `Nimble-v4` (9B) only if the hosted API is confirmed free. |

## Proposed technical defaults (listed in plans for review)

| ID | Proposal |
|---|---|
| P-01 | State template in chapter 03 (JSON text with `history`, `available_docs`, `query`). |
| P-02 | Option order fixed to the canonical order; no shuffling and no permutation averaging in round 1. |
| P-03 | Batch size 1 for latency; first 10 requests of each run are warm-up and excluded from latency statistics but still logged. |
| P-04 | Run every pipeline on **validation and test**. Headline numbers use test; validation exists so thresholds and temperatures can be fitted later without touching test. |
| P-05 | One run per configuration (models are deterministic, no sampling). Repeat only if latency variance looks suspicious. |
| P-06 | Repo layout and branch names in chapter 07 (`orchestrator/baselines-kev-0.8b` etc., see C-27; a branch named `orchestrator/baselines/kev` cannot coexist with `orchestrator/baselines` in git). |
| P-07 | Prediction log schema in chapter 06. |
| P-08 | Reference tokenizer for `input_tokens_ref`: the Qwen3.5 tokenizer (shared by Kev and Nimble). |
| P-09 | On Colab/Kaggle T4 GPUs (no native bf16, to be verified), prefer fp16/fp32 paths where a model's docs allow it; record the dtype used. |
| P-11 | State serializer detail: single-line JSON, default separators, `ensure_ascii=False`, keys in the order `available_docs`, `history`, `request` (`common/state.py`). |
| P-10 | Kev escalation order: 0.8B → 4B → 9B, stopping when the model no longer fits the hardware; 27B is not attempted. |

## Pending (agents must stop and ask)

X-04 is deferred by the owner until after the runs (logs store full distributions). X-05 is deferred until Nimble starts.

| ID | Question | Why it matters |
|---|---|---|
| X-04 | **Confidence definition and override scope.** Which per-question statistic (max probability, margin, Kev-style normalized confidence), how the per-record confidence aggregates, and whether `refuse` / `quick_reply` outputs are exempt from the low-confidence → agentic override. | Chapter 04. The log stores full distributions, so this can be decided after the runs. |
| X-05 | Is **quantization** allowed in the Nimble local fit check? | The Nimble README documents unquantized weights only. |

## Out of scope for round 1

Fine-tuning · τ tuning · S1/S2 baselines · cost analysis · the safety check itself (teammate) · the answer-writer Q&A dataset · hosted Jev · pseudonymisation of inputs · option-permutation studies.
