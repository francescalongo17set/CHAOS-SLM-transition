# 10 · Pipeline: Nimble

Branch: `orchestrator/baselines-nimble`. Read first: chapters 01–07. Facts come from the Nimble README (github.com/bespokelabsai/nimble) as of 12 Nov 2026 and a few search snippets of its docs. The training, scoring and deployment guides could **not** be opened directly (chapter 12). Read them yourself at the start of the task.

## What Nimble is

A typed-decision model: a LoRA on **Qwen3.5-9B**, trained with cross-entropy over the allowed answer tokens, scored from logits (no generation). The schema is **flat**: each field is an `enum` (a list of string choices) or a `boolean`. Each allowed answer has a one-token code; the scorer reads those logits and applies softmax.

Versions mentioned by the README:

| Version | Where | Notes |
|---|---|---|
| Bespoke-Nimble-9B (latest main) | Hugging Face | 8,192-token context, up to 255 choices per field, T=1.0 (no separate temperature fit). The original release is under the tag `original-2676`. |
| Bespoke-Nimble-9B-v2 | Hugging Face / Ollama | Uses a transferred temperature 2.179 by default (README). |
| Bespoke-Nimble-9B-v3 | Hugging Face | A **LoRA adapter** for Qwen/Qwen3.5-9B. #1 open model under 25B on the Decision Index per the README (6 Oct 2026). |
| Nimble-v4 (9B), v4-max (27B) | **Hosted API only** (console.bespokelabs.ai) | Not downloadable. |

L-03: use **v3** for the local fit check; **hosted v4** only if the owner confirms the API is free. Training data is synthetic English-style data over ten subject categories; nothing is documented for Italian.

## Decision tree (C-13)

```
Is the hosted API free and the owner has an API key?  (owner action; agents never create accounts or handle payment)
  yes → Path A: hosted run (v4). Then, optionally, still try Path B for comparability.
  no / unclear → Path B: local fit check on Kaggle/Colab.
Path B passes?
  yes → run Nimble-v3 locally.
  no  → DROP Nimble. The comparison states "dropped for hardware limits", with the evidence below.
```

As of the last check the owner found the console "unclear, requests sign-in" about pricing. So the default is Path B unless the owner says otherwise.

## Path B: local fit check (do this first)

Everything is time-boxed and free-tier only. Record each result in `fit_check.md`.

1. **Hardware facts.** Print `nvidia-smi`, `torch.cuda.get_device_name()`, `torch.cuda.is_bf16_supported()`, free RAM, free disk. The README requires a BF16-capable NVIDIA GPU for the CUDA scorer.
2. **Weights.** Nimble-v3 is an adapter: the pinned Qwen3.5-9B base (about 18 GB in bf16 per the README) must be downloaded, and the README's quickstart **merges the adapter on the CPU**, needing extra RAM and disk for both base and merged weights. Check RAM and disk against that before downloading. The README also describes running the adapter **without merging** on the CUDA path (see its `docs/NIMBLE_TRAINING.md`): read that document and write the method in your plan.
3. **Load test.** Try to load the model on the available GPU(s) with the README's `CudaCandidateScorer`. Record dtype, peak memory, errors. Kaggle's two T4s give 2×16 GB, but multi-GPU loading is not documented in the README; do not invent a sharding scheme without asking.
4. **Score test.** If it loads: score 20 validation rows end to end, record latency and peak memory.
5. **Verdict.** Pass only if the full request (all questions) completes for a pilot of 50 rows without OOM, without leaving the free tier, and within the session limits.
6. **Quantization** is not documented for the scorers (the MLX path "does not support quantized weights"). Using it changes the model under test. **Pending X-05: ask before trying.**

If any step fails, stop, write the evidence (exact error, memory numbers, device, available RAM/disk) and **drop Nimble** as the owner decided.

## Path A: hosted

- The owner supplies the key; read it from an environment variable or secret.
- Before writing code, read the Nimble agent skill: `plugins/nimble/skills/nimble/SKILL.md` in the repo (raw: `https://raw.githubusercontent.com/bespokelabsai/nimble/main/plugins/nimble/skills/nimble/SKILL.md`). It documents writing questions, choosing a model, error handling, acting on probabilities.
- Hosted latency includes network. Report it in a **separate, flagged row**, never in the same ranking as local runs.
- The README says the hosted API raised the prompt limit to 8,192 tokens per question, but the model was trained on prompts of up to 2,048 tokens, so shorter prompts are better tested.
- Log what the API returns for usage in `tokens.usage_reported`.
- Whether the hosted API returns full per-option probabilities is not established. If it returns only the chosen option, stop and ask (C-15 needs distributions).

## Interface (local scorers)

Schema per field (from the README example):

```python
schema = {
  "scope_check": {
    "type": "enum",
    "choices": ["in_scope", "out_of_scope", "quick_reply"],
    "description": "…",
    "choice_descriptions": {"in_scope": "…", "out_of_scope": "…", "quick_reply": "…"}
  }
}
result = scorer.score(state_text, schema)
result["output"]                              # {"scope_check": "in_scope"}
result["fields"]["scope_check"]["scores"]     # candidate probabilities
result["fields"]["scope_check"]["logits"]
```

Notes:

- The CUDA scorer scores each field with the **full prompt** every time (the shared context is processed again per field). The MLX scorer (Apple Silicon only) shares the prefix. We have no Mac, so count tokens accordingly: `input_tokens_native` is the sum over fields of the whole prompt.
- Each field is scored independently; fields cannot see each other.
- Enum choice limits conflict between docs: the README says 1–255 (latest checkpoint), the parallel-scoring doc says 1–26 (MLX path). Our largest question has 6 options, so both are fine, but do not rely on either for anything larger.
- Prompt token limits also differ: contract default 2,048, parallel-scoring doc 4,096, README 8,192. The scorer **rejects** over-length prompts rather than truncating. Check the audit's token lengths and log any rejection as an `error`.
- The scorer needs the model contract (`schema_config.json`) and the exact `revision` hash. Load config from `.cache/nimble-model.json` as the README does, and log the revision.
- The latest checkpoint and v3 use T=1.0 by default; v2 and the original release use 2.179. Log `temperature_applied` from the scorer, do not assume.
- "Boolean" fields exist, but chapter 03 uses `enum` only.

## Token and latency accounting

- `input_tokens_native`: Qwen3.5 tokenizer on each field's full prompt, summed over fields.
- `input_tokens_ref`: shared counter (same tokenizer, once).
- Latency: whole request (all fields), per chapter 05. Hosted is a separate flagged row.

## Implementation steps

1. Read the three Nimble docs you need: scoring guide, training guide (for no-merge loading), and the agent skill if Path A. Summarize in your plan what each says and where it disagrees with this chapter.
2. Run the fit check (Path B), or confirm Path A with the owner. Write the verdict.
3. If a path passes: adapter (chapter 03 → Nimble schema → canonical answers), 5-row unit test, pilot of 50 validation rows, full validation and test runs, report.
4. If both fail: write `dropped.md` with the evidence; the shared comparison script must accept a pipeline with no runs and print the reason.

## Acceptance criteria

- Either validated logs for validation and test, or a `dropped.md` with hardware evidence and a statement of what was attempted.
- `run.json` states checkpoint revision, adapter merged or not, dtype, device(s), latency mode (local or hosted).

## Stop-and-ask triggers

Pending X-05 (quantization) · hosted pricing unclear · hosted API lacks distributions · needing multi-GPU sharding · any step that needs paid compute · a prompt rejected for length on more than a few rows.
