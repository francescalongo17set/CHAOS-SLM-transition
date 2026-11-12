# 05 · Evaluation protocol

One shared script computes every number from the prediction logs (chapter 06) and the ground truth. Pipelines never compute metrics themselves.

## Splits

| Split | Use in round 1 |
|---|---|
| test (593) | Headline results. |
| validation (298) | Run too (P-04). Not reported as a headline; kept so thresholds and temperatures can be fitted later without touching test. |
| train (2,092) | **Not run** in round 1. |

## Applicability masks

| Output | Scored on |
|---|---|
| `scope_check` | all rows |
| `feature_classification` | all rows |
| `complexity_estimation` | rows with gold `scope_check == in_scope` |
| `needs_clarification` | rows with gold `scope_check == in_scope` (gold = `labels.missing_info` non-empty) |
| route (end-to-end) | all rows |

Complexity and slot questions are still *asked* for every row so probabilities are logged; they are simply not scored where the gold has no label.

## Quality metrics (C-09, C-06)

For each scored output:

- Accuracy.
- Per-class precision, recall, F1 and support.
- Macro-F1.
- Confusion matrix (saved as CSV, not necessarily shown in the report).

Specifics:

- `needs_clarification` is binary; report P/R/F1 of the positive class (needs clarification) and accuracy.
- **Route (end-to-end):** the dispatcher run on the model's *predicted* record with `tau=None` versus `support.expected_route`. Report the same metrics on the 5 routes, plus the per-route breakdown (L-02b).
- **Dispatcher oracle:** the dispatcher run on *gold* fields versus `expected_route` must be 100% (chapter 04). Report it as a sanity line, not as a model result.
- **Route attribution** (small table, no extra metric): for each wrong route, which earlier field was the first one wrong. It tells the owner where the errors enter.

## Kept extras (L-02)

1. **Recall on `refuse`** with a separate slice for rows with `safety_leak: true`, and a sub-slice by `leak_type`. These rows reproduce safety-checker misses (C-08), so recall on them is the number the owner will care about.
2. **Per-route breakdown** of the end-to-end route.
3. **ECE and Brier score**, computed on the probabilities **exactly as each model ships them** (no refit, no temperature change). 10 equal-width bins for ECE, on the `p_max` of each question. Report per question, not averaged across questions.

Anything else (pair consistency, order sensitivity, slices by noise tag, and so on) is **not** part of round 1 (C-20). The logs keep the fields needed to add them later.

## Token consumption (L-01)

| Field | Definition |
|---|---|
| `input_tokens_native` | Tokens the model actually processed for the request, counted with the model's own tokenizer, summed over all forward passes (all questions). If a runtime recomputes the shared state per question, that recomputation counts. If it reuses a cache, it counts once. State which one in the pipeline notes. |
| `input_tokens_ref` | Serialized state + question text (all questions) tokenized **once** with the reference tokenizer (P-08: Qwen3.5). Same number for any pipeline on the same row, which makes models comparable. |
| `output_tokens_native` | Logged if the runtime reports it; **not compared**, because no model generates text. Kev's API reports tokens of the serialized answers, which is not generation. |

Report per request: mean, median, p95, for both numbers. Report totals per split.

If a hosted API returns its own usage counts, log them as `usage_reported` and keep the two native/reference numbers too.

## Latency (C-10)

Definition: **wall-clock time for one request, from the moment the request is sent to the moment the whole response is received.** One "request" is one dataset row, producing the entire record (all questions).

Rules:

- Use `time.perf_counter()`; for GPU work make sure the call has finished (synchronize or rely on the call returning a CPU result).
- Batch size 1 (P-03). The first 10 requests of each run are warm-up: logged but excluded from statistics.
- Model loading and tokenizer loading are **not** inside the request time. Log load time separately per run.
- Where the model needs several calls per row (for example one per question or per field), the request time is the sum, because the record is only complete at the end.
- Report p50, p95, mean, and the number of requests.
- Local models are timed with an **in-process library call** (C-24); record `latency_mode` in `run.json`.
- Hosted APIs include network time. Report them in a separate row and mark the row **not comparable** with local runs.
- Latency numbers are comparable only between runs on the **same GPU type**. Always log the GPU name; compare like with like and say so in the report.
- Do not report the `latency_ms` returned by Kev's API as the latency metric: it is model time, not end-to-end. Log it as `usage_reported.latency_ms` if present.

## Model size (C-11)

Per model (and per size for Kev):

- Total parameters (base plus adapter plus head, counted from the loaded model, with the method stated).
- On-disk size of what had to be downloaded (adapter, base, or full checkpoint).
- Peak GPU memory during the run (`torch.cuda.max_memory_allocated()`), and dtype.
- Peak host RAM if it was a problem during loading (merging adapters can be RAM-heavy).

## Report format

Per pipeline run, the shared script writes `report.md` and `metrics.json`:

1. Run header: model id and revision hash, dtype, GPU, library versions, latency mode, split, number of rows, number of rows with errors or truncation.
2. Quality tables per output (accuracy, macro-F1, per-class P/R/F1).
3. Route tables and the refusal-recall slice.
4. ECE and Brier per question.
5. Tokens, latency, size table.

Then one cross-pipeline `comparison.md` that places the three pipelines side by side. Rows with different GPUs or latency modes are flagged, not hidden. If a pipeline was dropped (Nimble, chapter 10), the comparison states why, with evidence.

## Statistical care

With 593 test rows, differences of a point or two are noise. Do not rank pipelines on gaps below that without a paired test; no test is required in round 1, but the report must not claim a winner on tiny gaps.
