# 09 · Pipeline: Laya

Branch: `orchestrator/baselines-laya`. Read first: chapters 01–07. Facts come from the Laya model card on Hugging Face (convaiinnovations/laya) as of 12 Nov 2026. The GitHub README and notebooks were **not** read (chapter 12).

## What Laya is

A non-autoregressive decision model: a bidirectional encoder plus a small decision head trained from scratch (2 transformer layers, an option-marker scorer, an act/escalate head). Every question in a call is answered in **one forward pass**; it never generates text. Trained with a reinforcement-learning method for calibrated probabilities (RLCD). Apache-2.0.

| Checkpoint | Encoder | Params | Context | Notes |
|---|---|---|---|---|
| `convaiinnovations/laya` (repo root) | ModernBERT-large | 421M | 512 | English. Collapses on non-Latin scripts. |
| `laya-multilingual` (subfolder `multilingual`) | mmBERT-base | 322M | 1024 (up to 8k with `max_len=8192`) | 100+ languages. **Our choice (C-05).** |
| `laya-typed-decisions` | ModernBERT-large | 421M | 1024 | English, fine-tuned on the card's own four workflows. |

Disk: about 647 MB for the multilingual weights (card).

## The most important caveat

The card says the **base checkpoints are near chance zero-shot** on its own typed-decisions benchmark (0.362 and 0.342 accuracy against 0.461 for a majority-class baseline), and that the capability comes from fine-tuning. So a weak showing in round 1 is expected and is **not** a pipeline bug. Report it as measured, without tuning prompts to rescue it beyond the question-config discipline of chapter 03.

## Interface

```python
import laya
agent = laya.load("convaiinnovations/laya", subfolder="multilingual")   # direct, no routing
result = agent.predict(state, questions)
answers = result["answers"]
```

or

```python
from laya import Router
router = Router()   # lazy; Router(preload=True) loads all checkpoints
result = router.predict(state, questions, model="multilingual", max_len=1024)
```

**Use the explicit checkpoint** (`laya.load(..., subfolder="multilingual")` or `model="multilingual"`). The `Router` picks English vs multilingual by script and language detection; the card warns that mostly-English text routes to the English checkpoint, and our rows mix Italian with English terms. A silent switch would change the model under test. Log `result["routing"]` if the Router is used, and fail the run if it ever selects another checkpoint.

Question format (same shape as the Jev API):

```python
questions = {
  "scope_check": {"type": "choice", "instructions": "…",
                  "criteria": {"in_scope": "…", "out_of_scope": "…", "quick_reply": "…"}},
}
```

Result: `result["answers"][id]["choice"]`, with a confidence value; the card's example shows `confidence: 0.94` per answer. The card does not show the full per-option probability field name in its snippets. **Inspect a real result object and write down the key that holds the full distribution before writing the adapter.** If it only exposes the chosen option's confidence, stop and ask (the full distribution is mandatory, C-15).

## Known issues from the card, and what to do

| Issue (card) | Handling |
|---|---|
| Base checkpoints ship **over-confident**. | Use probabilities as shipped (L-02c); report ECE; do not refit. |
| `noul` can follow its option labels rather than the text (issue #156). | Use only 2-or-more-option `choice` questions (chapter 03). |
| `action.act_probability` carries no usable signal (issue #185). | Ignore it. Do not use it as confidence. |
| Option text shares a fixed `head_max_len` budget (256 tokens for multilingual). With many options each gets few tokens; Banking77 with 77 options collapsed to 0.425. | Our largest question has 6 options. Keep descriptions short. If you must raise `agent.cfg["head_max_len"]`, ask first (changes the model's input budget) and log the value. |
| Default `max_len` for multilingual is 1024, i.e. about 768 tokens for the state (1024 minus `head_max_len` 256). Longer inputs are **cut off**. | Count the state tokens in the audit. For rows over budget, either use `max_len=8192` (documented, results vary beyond ~4,000 tokens) or log `truncated: true` and `tokens_dropped`. Ask the owner which if more than a few rows exceed the budget (chapter 02 audit). |
| `laya.load()` can hang if TensorFlow is installed. | Set `USE_TF=0`. |
| Ordinal `score` questions are the weakest primitive. | Not used. |

## Install and run

```
pip install laya        # Python 3.10+
# extras: laya[serve] (HTTP server), laya[onnx], laya[fast] (TileLang GPU fast path)
```

HTTP alternative: `laya-serve` exposes `POST /v1/systemone` in the same shape as TypeSafe Jev (default `0.0.0.0:8000`, no auth unless `LAYA_API_KEY` is set; env `LAYA_DEVICE=cuda`, `LAYA_PRELOAD=1`). Which one is used for latency is pending (X-03).

Speed reference from the card (Tesla T4, multilingual): 32.8 ms for 1 question, 40.1 ms for 5, 72.3 ms for 10. Treat as a sanity check against your own measurements, not a target.

## Token accounting

Laya is an encoder. Count tokens with its own tokenizer on exactly the strings it encodes. Because all questions share one pass, report both: the state once, plus the per-question option text. Document precisely how you counted (the encoder input is the state plus the question block). `output_tokens_native` is `null`.

## Calibration state

The card says the checkpoints ship over-confident and that refitting one temperature per (question type, option count) on your own data moves mean ECE from 0.314 to 0.106 for `laya-multilingual`. Round 1 does **not** refit. Store `temperature_applied: null` unless the runtime reports one.

## Implementation steps

1. **Smoke test.** `USE_TF=0`, install, load the multilingual checkpoint, answer one question from the card on a short Italian string. Print the entire result object.
2. **Adapter.** Canonical question config → Laya `questions`; result → canonical `answers` with full distributions. Unit-test on 5 rows, one per route.
3. **Budget check.** Count how many validation and test rows exceed the multilingual state budget; decide with the owner how to handle them.
4. **Pilot, full runs, report** exactly as in the Kev chapter (steps 4, 5, 7). Single model, no escalation.

## Acceptance criteria

- Logs pass the shared validator; the checkpoint is the multilingual one for every row.
- Full probability distributions stored; truncation logged.
- `run.json` states checkpoint revision, `max_len`, `head_max_len`, device, latency mode.

## Stop-and-ask triggers

Pending X-01, X-02, X-03 · distribution key not found · any row routed to the English checkpoint · over-budget rows beyond a handful · need to change `head_max_len`.
