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

### route, end-to-end (tau=None)

n = 298 · accuracy 0.393 · macro-F1 0.395

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.438 | 0.594 | 0.504 | 101 |
| agentic | 0.533 | 0.195 | 0.286 | 123 |
| refuse | 0.189 | 0.292 | 0.230 | 48 |
| quick_reply | 0.452 | 0.731 | 0.559 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 115 |
| feature_classification | 52 |
| complexity_estimation | 14 |

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

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 572.0 | 539.5 | 766 | 170470 |
| input_ref | 298 | 392.4 | 381.5 | 454 | 116946 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 32.4 | 31.5 | 38.0 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 321908995, 'params_method': 'sum of numel over agent.model.parameters() (encoder + decision head)', 'disk_mb': 678.2, 'peak_gpu_mem_mb': 1532.0, 'peak_host_ram_mb': 2958.6}
