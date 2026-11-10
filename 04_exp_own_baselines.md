# 04. Experiments: our own baselines (S1 generative, S2 decision readout)

Status: DRAFT v0.1. Read `00_overview_and_rationale.md` and `01_data_spec_and_generation.md` first.

These are **our designs**, not repo features. They are grounded in the LLM-as-Jev paper (P1, https://arxiv.org/pdf/2610.02076), which documents the readout idea, a fine-tuning recipe and measurements. Where we deviate from P1, the step says so. Nothing here is a documented property of Kev or Nimble.

## 1. Goal

Compare, on the same data and test set:

- **S2-zero:** readout from a frozen model, no training.
- **S2-LoRA:** the same readout after a LoRA fine-tune.
- **S1:** one model generating the whole record as constrained JSON (zero-shot and LoRA).

and report accuracy, calibration, and latency (file 05).

## 2. Existing drafts

`orchestrator_data.py` and `orchestrator_readout.py` (in the parent folder) are our earlier drafts: label spaces, prompts, option shuffling, balancing, a readout function, loss, temperature fitting, ECE, Brier, thresholds. **They were never run against a real model.** An agent may reuse or rewrite them, but must test them first. `[OUR DECISION]`

## 3. What P1 documents (use as the reference, do not extend)

- **Readout idea.** Put the question and numbered options in the prompt, end the assistant turn with a fixed prefix, and score each option's completion from next-token probabilities; no text is generated. Prompt format: `State: {s}`, `Options:` as `[1] ... [K]`, then `Select one option. Answer only with its bracketed numeric identifier.`; chat template with thinking disabled; assistant prefix `Best answer: [`; each option is the suffix `k]`. `[DOC: P1 §3.2, App. A]`
- **Letter readouts** (reading the logits of the option letters) are used by several community models. `[DOC: P1 §2]` P1 notes they are limited to about 26 options; ours has at most 6. `[DOC: P1 §3.2]`
- **Zero-shot results.** On Qwen3.5-4B the training-free readout scored 81.4% on its public benchmark with ECE 0.057; plain generation scored the same 81.4%. On Qwen3-0.6B: 56.7% (ECE 0.278). `[DOC: P1 Table 1]`
- **Cost in passes.** Readout: a prefill plus about 2 sequential forward passes; thinking (budget 512 to 4,096 tokens): 464 to 1,824 passes. `[DOC: P1 Table 17]`
- **Fine-tuning recipe.** Listwise loss on the gold option plus KL anchors against the frozen base model; LoRA rank 16, alpha 32, dropout 0, on all decoder linear layers; learning rate 1e-4 for LoRA; AdamW, weight decay 0.01, gradient clipping 1.0; linear warmup (10% of steps; 100 for one-epoch runs) then linear decay to 10% of the peak; one pass over the data; global batch 32; shuffled option order; gradient checkpointing; maximum length 8,192. `[DOC: P1 Table 2]` (P1 trained with FSDP on four A100 GPUs, which we do not have `[DOC: P1 App. B]`.)
- **Results of fine-tuning (4B).** LoRA with anchors (lambda = 1) reached 84.0% accuracy and ECE 0.050; LoRA with lambda = 0 reached 82.3% with ECE 0.070 (single seed). `[DOC: P1 Table 11]`
- **Why anchors.** Without anchors, the fine-tuned 4B model kept writing text after the answer on 69 of 231 items in text mode. `[DOC: P1 §4.4]` This matters only if the model must also generate text (S1).
- **Data lessons.** Training only on intent data biased the model toward "yes" (affirmative predictions 36 to 49 against 35 gold) and raised ECE from 0.057 to 0.134; balanced reasoning data fixed it; short-only data hurt long inputs. `[DOC: P1 App. G]`
- **Thinking.** Thoughts up to 256 tokens gave no gain; 512 tokens: 84.8%; 1,024: 89.2%; 4,096: 94.8% (base 81.4%). Median latency rose from 0.2 s to 15.6 s at 512 tokens (FP32, an RTX A5500, unoptimised). `[DOC: P1 Table 16]`

## 4. Common decisions

`[OUR DECISION]`

- **Backbones:** the two backbones evaluated in P1 so that its numbers are a reference: Qwen3.5-4B and Qwen3-0.6B (model cards cited in P1: `Qwen/Qwen3.5-4B`, Qwen3-0.6B). Whether the 4B model can be trained on the free tier `[NOT DOCUMENTED]`: run the smoke test (section 7). Start with the 0.6B model.
- **Pipeline order:** `scope_check`, then `feature_classification`, then `complexity_estimation` and the slot questions of the predicted feature. Short-circuit: stop after `scope_check` when it is not `in_scope`, and skip the rest when `feature_classification` is `none`.
- **Prompts:** keep the prompt template identical across S2 variants; log it with the results.
- **Probability bookkeeping:** every run stores, per test example and per field, the probability vector in canonical label order (not in shuffled option order), so file 05 can compute all metrics.

## 5. Experiment S2: decision readout

### S2-zero (no training)

1. Load the backbone in the dtype supported by the GPU (test; see `00`). Use the model's chat template with thinking disabled (as P1). `[DOC: P1 App. A]`
2. Build the prompt for each field with `orchestrator_data.build_prompt`-style templates (letters A to F). `[OUR DECISION]` P1's numeric `[k]` interface is the documented alternative; run it as an ablation if the letter readout shows strong position bias.
3. Check that each option letter is a single token for the tokenizer; if not, stop and report. `[OUR REQUIREMENT]`
4. Read the next-token logits at the last position (left-pad batches), restrict to the option tokens, softmax. `[OUR DECISION, standard letter readout described in P1 §2]`
5. Evaluate with three option orders per field (identity, reversed, one random) and average probabilities mapped back to canonical order; report the answer-change rate across orders. (P3 found that reversing the option order changed 30% of one model's answers and 1.8% of another's. `[DOC: P3 §5]`)
6. Save per-example probabilities. Run on calibration and test.

### S2-LoRA

1. Data: file 01 train split, expanded to one training example per field (and per slot), with **fresh random option order every epoch**. `[OUR DECISION based on P1 §3.4]`
2. Balance classes per field (cap at 2x the rarest). `[OUR DECISION]`
3. Loss: cross-entropy over the option-letter logits only, at the last position. `[OUR DECISION; P1 uses a listwise loss over option suffixes, equivalent in spirit for single-token options]`
4. LoRA: start from P1's settings (rank 16, alpha 32, dropout 0, all decoder linear layers, learning rate 1e-4, weight decay 0.01, clip 1.0, 10% warmup, linear decay to 10%, one epoch). `[DOC: P1 Table 2]` Global batch 32 is P1's value; on small GPUs use gradient accumulation to reach it, or document the batch actually used. `[OUR DECISION]`
5. Anchors: not required for a pure readout. Optional ablation: add a KL penalty against the frozen base model on the answer position (P1 anchors more positions, with top-64 truncation; copying that exactly is `[NOT DOCUMENTED]` here beyond P1's description). The 4B LoRA result above (ECE 0.050 with anchors vs 0.070 without) is the reason to try it. `[DOC: P1 Table 11]`
6. After training, run the same evaluation as S2-zero and the diagnostic from file 01: for each class, predicted count vs gold count (a class predicted much more often than it occurs signals bias). `[DOC: P1 App. G for the diagnostic]`
7. Fit temperature per field on the calibration split (grid search minimizing NLL); report ECE and Brier before and after. `[OUR DECISION]`

## 6. Experiment S1: generative record

All of this is `[OUR DECISION]`; none of the sources we read specify the generative baseline.

1. Output format: compact JSON, one key per field, label strings only; for slots, a list of the missing or ambiguous slot names. Keep it short: every generated token costs one sequential pass. `[DOC: P1 Table 17 for cost per pass; decision is ours]`
2. Decoding: greedy, with grammar or schema-constrained decoding so the output always parses. The constrained-decoding library `[NOT DOCUMENTED]` in our sources: choose one, record name and version, and verify that it works on the GPU in use.
3. Confidence: the probability of each label token in the generated JSON (token log-probs), taken at the position of the label's first distinguishing token. `[OUR DECISION]` For slot lists, use the minimum over the slot decisions.
4. Zero-shot S1: instruct prompt with the label definitions and the JSON schema; evaluate on calibration and test.
5. S1-LoRA: supervised fine-tuning on the target JSON, loss on the answer tokens only, same LoRA settings as S2-LoRA, same data. If the model must keep general generation ability, add the anchors from P1 (§4.4 shows why). `[DOC: P1 §4.4]`
6. Report failure modes: invalid JSON rate (should be zero with constrained decoding), trailing text, and inconsistent combinations (for example `scope_check = out_of_scope` with a feature).

## 7. Smoke tests and checkpoint contract (mandatory)

`[OUR REQUIREMENT]`, see `00` section 5.

- **Smoke test:** 20 to 50 training examples, 5 steps: record GPU, dtype that works, peak memory, step time, tokens per second. Run it for the 0.6B and, if it fits, for the 4B. If the 4B smoke test runs out of memory, stop and report; do not switch to quantization or other tricks without a team decision.
- **Checkpoints:** save the LoRA adapter, optimizer state, scheduler state, RNG state and the data-order seed every N steps (N from the measured step time, about 10 minutes of training) and at each epoch end. Write atomically. Keep `STATE.json` (step, epoch, seed, config hash, data hash, commit hashes).
- **Resume:** on start, load the latest checkpoint and the exact data order (derive the order from the seed and the epoch, so it is reproducible); log how many steps were redone.
- **Evaluation jobs** write each prediction as soon as it is computed (append to JSONL), and skip examples already present on restart.
- **Hardware log:** GPU, memory, driver, library versions, at the start of every job; store with results.

## 8. Fallback ladder experiment (optional, after S2-LoRA)

Goal: measure whether budgeted thinking helps on low-confidence fields.

1. Choose thresholds per field on the calibration split (file 05).
2. For examples below the threshold, re-run the field with thinking under a hard token budget, then read out the options. Documented procedure (P1 Appendix K): chat template with thinking enabled; greedy decoding; stop at the model's end-of-thinking marker or after N tokens; close the thought with a line break, the end-of-thinking tag and two line breaks; append the answer prefix; score the options. `[DOC: P1 App. K]` The prompt addition used there: a sentence limiting thinking to N tokens. `[DOC: P1 App. K]`
3. Budgets to try: 512 and 1,024 (smaller budgets gave no gain in P1). `[DOC: P1 Table 16]`
4. Report accuracy gain on the escalated subset, the fraction escalated, and the added latency on our hardware.
5. Final fallback: fail safe (complexity and sensitive features to the Agentic path; `missing_info` to clarification). `[OUR DECISION]`

## 9. Deliverables

- Per-example probability files (canonical order) for every system, split and run.
- Trained adapters, fitted temperatures, thresholds, `STATE.json`, logs, hardware logs.
- `RESULTS_NOTES.md` with every `[NOT DOCUMENTED]` finding.
- The filled comparison table from `05_evaluation_protocol.md`.

## 10. Risks

- P1's gains are on public benchmarks; our domain and language differ.
- `complexity_estimation` zero-shot may be near chance (P3 found zero-shot routing at chance for both models tested). `[DOC: P3 §5]`
- Single-seed results are noisy (P1 states single-seed runs; one to two points on individual benchmarks can be variance). `[DOC: P1 App. H]` Run at least two seeds for the final systems if time allows. `[OUR DECISION]`
