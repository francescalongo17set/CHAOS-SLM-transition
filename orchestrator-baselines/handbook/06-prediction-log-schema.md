# 06 · Prediction log schema (PROPOSED, P-07)

Every pipeline writes the **same** JSONL, one line per request. The shared evaluation script reads only this file and `router.jsonl`. This is what makes three independently built pipelines comparable.

Path: `runs/<pipeline>/<run_id>/<split>.jsonl`, plus `runs/<pipeline>/<run_id>/run.json` (run-level metadata, below).

## Per-request line

```jsonc
{
  "run_id": "kev-0.8b-20261115-a",
  "pipeline": "kev" | "laya" | "nimble",
  "model_id": "jaredpalmer/kev-0.8b",
  "model_revision": "<hf commit hash or tag>",
  "split": "test",
  "query_id": "orc-002403",
  "pair_id": null,

  "answers": {
    "scope_check":            {"label": "in_scope",
                               "probs": {"in_scope": 0.93, "out_of_scope": 0.05, "quick_reply": 0.02},
                               "option_order": ["in_scope", "out_of_scope", "quick_reply"]},
    "feature_classification": {"label": "product_policy_analysis", "probs": {...}, "option_order": [...]},
    "complexity_estimation":  {"label": "simple", "probs": {...}, "option_order": [...]},
    "slots": {
      "insurer":  {"label": "present", "probs": {"present": 0.9, "missing": 0.05, "ambiguous": 0.05}, "option_order": [...]}
    }
  },
  "slots_asked_for": "predicted_feature",   // C-23; the validator also accepts "gold_feature" and "all" for later studies
  "needs_clarification": false,

  "temperature_applied": 2.41,          // null if the runtime reports none; "raw" if forced to 1.0
  "latency_ms": 312.4,                  // wall clock, request sent to full response (chapter 05)
  "is_warmup": false,
  "tokens": {
    "input_native": 842,
    "input_ref": 790,
    "output_native": null,
    "usage_reported": {"input_tokens": 101, "output_tokens": 161, "latency_ms": 495}   // raw from API/library, if any
  },
  "truncated": false,
  "tokens_dropped": 0,
  "error": null                          // string if the call failed; answers may then be null
}
```

Rules:

- `probs` keys are the canonical option ids from chapter 03, **in the order shown to the model** (`option_order`). Probabilities must sum to 1 within 1e-3; the shared script rejects the file otherwise.
- Never store only `argmax`. Full distributions are mandatory (C-15).
- If a call fails, write a line with `error` set and `answers: null`. Never drop rows silently; the script reports the error count and counts them as wrong.
- If a runtime returns **logits** instead of probabilities, store the probabilities used in the final output and add `"logits"` beside `probs` so a temperature can be refit offline.
- If a runtime applies its own temperature (Kev, Nimble v1/v2), store `temperature_applied`. If you can also obtain raw probabilities without re-running (for example from logits), add `probs_raw`. If getting raw requires a second run, **do not** do it in round 1 (the shared script uses the probabilities as shipped, L-02c).

## Run-level `run.json`

```jsonc
{
  "run_id": "...", "pipeline": "...", "model_id": "...", "model_revision": "...",
  "dtype": "fp16|bf16|fp32", "device": "Tesla T4", "gpu_count": 1,
  "python": "3.12.x", "libraries": {"torch": "...", "transformers": "...", "kev": "<git sha>", "laya": "..."},
  "platform": "kaggle|colab|local",
  "latency_mode": "in_process|http_local|http_hosted",
  "question_config": "questions.en.yaml (sha256 ...)",
  "state_template": "p-01",
  "data_manifest_sha256": {"test": "...", "validation": "..."},
  "load_time_s": 41.2,
  "model_size": {"params_total": 0, "params_method": "...", "disk_mb": 0, "peak_gpu_mem_mb": 0, "peak_host_ram_mb": 0},
  "started_at": "...", "ended_at": "...",
  "notes": "free text: anything surprising"
}
```

## Validation by the shared script

Before computing any metric the script checks: one line per `query_id` of the split (no gaps, no duplicates), all options present, probabilities sum to 1, `answers` keys complete for the rows' scope, and `latency_ms` present for non-error rows. Failure → the run is not accepted.
