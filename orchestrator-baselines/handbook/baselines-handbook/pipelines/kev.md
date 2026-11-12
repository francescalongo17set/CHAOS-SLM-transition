# 08 · Pipeline: Kev

Branch: `orchestrator/baselines-kev`. Read first: chapters 01–07. Facts below come from the Kev README (github.com/jaredpalmer/kev) as of 12 Nov 2026; see chapter 12 for what is unverified.

## What Kev is

A family of Jev-style decision models: a LoRA adapter (rank 16) plus a small **pointer head** on a Qwen base. It reads a state and typed questions in one sequence and returns, per question, a probability distribution over the options. No text generation. Apache-2.0.

| Size | Base | Notes (from the README) |
|---|---|---|
| Kev-0.8B | Qwen3.5-0.8B-Base | Runs on an L4 or "any 4 GB GPU". Validated context 8,192 tokens. Shipped temperature 2.35. **Start here (C-05).** |
| Kev-4B | Qwen3.5-4B-Base | Listed for L40S/H100 or a 32 GB Mac. Shipped temperature 2.41. |
| Kev-9B | Qwen3.5-9B-Base | Needs about 17 GB GPU memory (README). Shipped temperature 2.19. |
| Kev-27B | Qwen3.8-27B (full weights, 51 GB) | Needs an 80 GB GPU. **Not attempted.** |

The Kev-0.8B Hugging Face card lists English only. Expect weak zero-shot Italian; that is a result to report, not a bug.

## Interface

Kev follows the TypeSafe System One API. Question types: `noul` (yes/no), `choice` (1–255 options, each with an optional description), `score`. Round 1 uses `choice` only (chapter 03).

Request (HTTP `POST /v1/systemone`):

```json
{
  "state": "<state text or JSON>",
  "model": "kev-latest",
  "questions": {
    "scope_check": {
      "type": "choice",
      "instructions": "…",
      "criteria": {"in_scope": "…", "out_of_scope": "…", "quick_reply": "…"}
    }
  }
}
```

Response per question: `choice`, `confidence`, `probabilities` (all options). Plus `usage.input_tokens`, `usage.output_tokens` (tokens of the serialized answers, **not** generated tokens) and `latency_ms` (model time only).

`confidence` for K>1 options is `(p_max − 1/K)/(1 − 1/K)`. It is not a measured accuracy rate (README).

State handling: an object or array state is converted to labelled text; delimiter-like strings in the input are escaped. A state longer than 65,536 tokens returns HTTP 422 (not truncated unless `KEV_TRUNCATE_STATES=1`). Our states are far below that.

## How it processes questions (matters for token counting)

On Qwen3.5 bases (every current Kev) each question runs as its **own row**: state followed by that question. The server computes the state once and reuses its cache for every row. Therefore, for `input_tokens_native`, count the state once plus each question's own tokens if the runtime reuses the cache; confirm what `usage.input_tokens` counts by running one request with 1 and with 4 questions and comparing. Record the finding in `run.json.notes`.

Questions are isolated: one question's answer cannot see another's. Options **within** a question can influence each other, and option order can change an answer (README, Limitations). We use a fixed order in round 1 (P-02).

## Install and run

Two ways. Which one is used for latency is pending (X-03).

**Local server** (README quick start):

```
git clone https://github.com/jaredpalmer/kev.git && cd kev
uv sync --extra serve
uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
```

Environment variables of interest: `KEV_TEMPERATURE=1.0` (raw probabilities instead of calibrated), `KEV_DTYPE=fp32` (exact fp32 path; GPU default is bf16), `KEV_API_KEY`. `--run` also accepts a Hub revision such as `jaredpalmer/kev-0.8b@v1.0`. **Pin the revision** and log it. The README's Kev 1.0 table lists tag `v1.0` per repo.

**Python SDK against the server** (`typesafe_sdk` installed by `uv sync --extra serve`): `TypeSafeClient(api_key="local", base_url="http://127.0.0.1:8009", model="kev-latest")`, then `client.system_one(state=..., questions={...})`.

**In-process library** (`kev.model.DecisionModel.probs()` is mentioned in the README's How It Works): the README does not give a usage example. If you choose this route, read `kev/model.py` and `tests/test_model.py` first and write down the call in your plan.

## Hardware notes for Kaggle/Colab (to verify in session)

- T4 lacks native bf16. For Kev-0.8B, serving in fp32 (`KEV_DTYPE=fp32`) is the documented exact path; 0.8B in fp32 is small enough for 16 GB. Record which dtype produced the numbers. The README says bf16 serving differs from the fp32 evaluation path by at most about 0.03 in probability and flips the top answer on about 1 in 300 questions.
- `flash-linear-attention` must be installed on CUDA for the Qwen3.5 models (README).
- Kev-4B: bf16 weights are about 8.4 GB; fp32 would be about 16 GB and will not fit one T4. Decide dtype before running, and log it.
- Kev-9B: about 17 GB of GPU memory per the README; does not fit one 16 GB T4. A Kaggle T4×2 might, but multi-GPU is not documented for `kev.serve`. If it does not fit, report it as not run (X-06).

## Calibration state

Kev ships a **fitted temperature** in each checkpoint, so its probabilities are calibrated by default (on public datasets, not ours). Round 1 uses them exactly as shipped (L-02c) and logs `temperature_applied` from the checkpoint. Do not fit anything.

## Implementation steps

1. **Environment smoke test.** Install, start the server (or load in-process), answer one question from the README example. Log versions, device, dtype.
2. **Mapping.** Implement `kev/adapter.py`: canonical state + question config → Kev request; Kev response → canonical `answers` (chapter 03/06). Unit-test on 5 hand-picked rows, one per route (use `query_id`s from the audit).
3. **Token accounting.** Implement `input_tokens_native` per the finding above, and `input_tokens_ref` via the shared counter.
4. **Pilot.** 50 validation rows. Record latency (chapter 05), tokens, peak GPU memory, any 422/errors.
5. **Full runs** on validation and test for Kev-0.8B; validate logs with the shared script.
6. **Escalate** (C-05, P-10): repeat steps 4–5 for Kev-4B, then Kev-9B if it fits. If a size does not fit, stop and report exactly where (OOM message, memory numbers).
7. **Report** with the shared script.

## Acceptance criteria

- Logs pass the shared validator for validation and test, for every size that ran.
- Probabilities in the logs are the ones returned by Kev with its shipped temperature.
- No row silently missing; error rows are logged.
- `run.json` states dtype, device, latency mode, Kev revision.

## Stop-and-ask triggers

Pending X-01, X-02, X-03, X-06 · any mismatch between the README and the installed package · a size that only fits in a configuration the README does not describe · a state longer than the model's validated context.
