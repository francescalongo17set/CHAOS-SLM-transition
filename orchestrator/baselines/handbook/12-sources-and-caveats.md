# 12 · Sources and caveats

All external facts in this handbook come from the pages below, read on **12 Nov 2026**. Anything not listed here is general knowledge and is labelled as such where used.

## Sources actually read

| Source | What was read | Used in |
|---|---|---|
| github.com/jaredpalmer/kev (README) | Full README: models table, API, quick start, fine-tuning, serving performance, limitations. | Chapter 08 |
| huggingface.co/convaiinnovations/laya (model card) | Full card: checkpoints, quickstart, Router, server, architecture, benchmarks, honest limits. | Chapter 09 |
| github.com/bespokelabsai/nimble (README) | Full README: capabilities, quickstart (MLX and CUDA), methodology, dataset, evaluation, temperature, latency, folder layout. | Chapter 10 |
| Project files | `orchestrator_experiment_references.md`, `orchestrator_data.py`, `orchestrator_readout.py`, folder README. | Chapters 02–04 |
| Test sample (`orc-002401` to `orc-003087`) | Row shape, label spaces, routes, slot lists. | Chapter 02 |
| Search snippets only | Nimble `PARALLEL_SCORING.md` (MLX), Hugging Face pages of Nimble-v3 and of Kev-0.8B (and derivatives), third-party pages about Nimble. | Chapters 08, 10 |

## Not read (agents must read at the start of their task)

- Nimble: `docs/NIMBLE_TRAINING.md`, `docs/MODAL_SERVING.md`, `docs/TRY_NIMBLE.md`, `plugins/nimble/skills/nimble/SKILL.md`, and anything under `console.bespokelabs.ai` (it requires sign-in).
- Kev: the model cards under `docs/model-cards/`, `skills/kev-finetune/README.md`, `kev/model.py`, `kev/serve.py`.
- Laya: the GitHub README (github.com/NandhaKishorM/laya), its docs site, and the Kaggle fine-tuning notebook. The model card's snippets do not name the field that holds the full probability distribution.
- The papers referenced in the project's `orchestrator_experiment_references.md` were read by the earlier author, not for this handbook.

The fetch tool used for scouting refused every sub-link of a page already fetched; only search results could be opened. That is why the deeper docs above are missing.

## Known contradictions and unverified claims

| Topic | What the sources say | Handling |
|---|---|---|
| Nimble enum choice limit | README: 1–255 (latest). `PARALLEL_SCORING.md` snippet: 1–26 (MLX). | Irrelevant for ≤6 options; do not rely on either for more. |
| Nimble prompt limit | README: 8,192 (latest) and 2,048 trained. Parallel-scoring doc: default 4,096. Contract default 2,048. | Audit token lengths; log rejections. |
| Nimble temperature | Latest checkpoint T=1.0; v2 and original release 2.179. v3's default is not stated explicitly. | Log `temperature_applied` from the scorer. |
| Nimble hosted pricing | Not found in any source. | Owner checks the console; default to the local fit check. |
| Kev-0.8B language | Card tag lists English. The README does not discuss Italian. | Treat Italian zero-shot as an open empirical question. |
| Laya full distribution field | Card shows `choice` and a confidence value, not the key for all probabilities. | Inspect the real result object. |
| Kev-0.8B revision | README table: weights revision `9a45d25e`. The run on 12 Nov loaded `@v1.0` and got Hub commit `bf75a6a8…` (= `main`, commit title "Kev 1.0 model card (weights unchanged)"); on 13 Nov the tag `v1.0` points to `788ddbdd…`, which is not on `main`'s history. **Checked 13 Nov (Hub API):** `adapter_model.safetensors` (sha256 `9b908623…1885a`) and `head.pt` (sha256 `f400bd12…0e6`) are identical in all three commits, so the weights are the model card's. Not checked: the GitHub release checksums, and whether the tag moved after our run. | Tags are movable: pin the commit `9a45d25eb2ab761841196625383fa1dff0e56c1e` (the notebook now does) and log `weights_sha256` in `run.json`. |
| Kev on Kaggle T4 | Smoke run: torch 2.8.0+cu128 works on a T4; `causal_conv1d` was not installed, so Transformers used its slower PyTorch path (README says it is correct but slower). | Latencies of the Kev-0.8B run are for that path; label them in the report. |
| Kev disk size | `run.py` recorded the adapter only (65.5 MB); base model is about 1,747 MB (Hub API, not measured on Kaggle). | `run.json` of the 0.8B run corrected by hand; `run.py` now records both. |
| T4 and bf16 | General knowledge (T4 has no native bf16), not from a source. | Verify with `torch.cuda.is_bf16_supported()` and measured speed in the session. |
| Kaggle/Colab limits | General knowledge. | Verify in the session; log the device. |

## Upstream numbers worth knowing (not our results)

These are the publishers' own figures on their own data. They are context, **not** expectations for Italian insurance requests.

- Kev (README, "new sources" test): Kev-0.8B 0.697 accuracy, Kev-4B 0.838, Kev-9B 0.852, Kev-27B 0.889. Kev-4B answers six questions in 18.1 ms on an H100 and 41.5 ms on an L40S (model time).
- Laya (card): base checkpoints near chance on typed-decisions (0.342–0.362); fine-tuned `laya-typed-decisions` 0.766; about 32.8 ms per question on a T4.
- Nimble (README): Bespoke-Nimble-9B 90.1% agreement on its own 324 held-out synthetic examples; median 106 ms per example on an H100 (120 examples), 444 ms on an M5 Pro Mac.

## Related project references

The project's `orchestrator_experiment_references.md` lists design choices and papers for the later fine-tuning stage (LoRA recipe, option shuffling, per-field temperature scaling, per-question thresholds). They apply **after** round 1. They are not instructions for this round.
