# Report · laya · validation

## Run header

- model: `convaiinnovations/laya/multilingual` @ `85cc74ddae6109077ebe2853a9b3077fb6606a78`
- dtype fp16 · device Tesla T4 · latency mode in_process
- libraries: {'laya': '0.4.31', 'torch': '2.11.0+cu130', 'transformers': '5.20.2'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.614 · macro-F1 0.509

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.824 | 0.670 | 0.739 | 224 |
| out_of_scope | 0.189 | 0.292 | 0.230 | 48 |
| quick_reply | 0.452 | 0.731 | 0.559 | 26 |

### feature_classification

n = 298 · accuracy 0.406 · macro-F1 0.396

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.179 | 0.385 | 0.244 | 39 |
| product_policy_analysis | 0.374 | 0.521 | 0.435 | 71 |
| comparison | 0.769 | 0.250 | 0.377 | 40 |
| ibip_screening | 0.091 | 0.054 | 0.068 | 37 |
| client_drafting | 0.771 | 0.730 | 0.750 | 37 |
| none | 0.667 | 0.405 | 0.504 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.522 · macro-F1 0.394

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.519 | 0.957 | 0.673 | 115 |
| complex | 0.583 | 0.064 | 0.116 | 109 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 224 · accuracy 0.308 · macro-F1 0.307

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.210 | 0.760 | 0.329 | 50 |
| False | 0.721 | 0.178 | 0.286 | 174 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.238 · macro-F1 0.254

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.290 | 0.098 | 0.146 | 92 |
| agentic | 0.375 | 0.037 | 0.067 | 82 |
| clarification | 0.182 | 0.520 | 0.269 | 50 |
| refuse | 0.189 | 0.292 | 0.230 | 48 |
| quick_reply | 0.452 | 0.731 | 0.559 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 115 |
| feature_classification | 60 |
| needs_clarification | 52 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.292 |
| safety_leak | 18 | 0.333 |
| non_leak | 30 | 0.267 |
| leak: data_extraction | 2 | 0.500 |
| leak: fraud_or_illegal | 3 | 0.667 |
| leak: jailbreak | 2 | 0.500 |
| leak: prompt_injection | 9 | 0.222 |
| leak: social_engineering_or_abuse | 2 | 0.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.135 | 0.522 |
| feature_classification | 298 | 0.320 | 0.867 |
| complexity_estimation | 224 | 0.329 | 0.724 |
| slots (pooled, where gold slot status exists) | 379 | 0.405 | 0.999 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 941.7 | 954.5 | 1527 | 280623 |
| input_ref | 298 | 567.4 | 587.0 | 744 | 169072 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 57.8 | 60.5 | 69.8 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 321908995, 'params_method': 'sum of numel over agent.model.parameters() (encoder + decision head)', 'disk_mb': 678.2, 'peak_gpu_mem_mb': 1532.3, 'peak_host_ram_mb': 2953.1}
