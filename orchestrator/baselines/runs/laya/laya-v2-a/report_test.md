# Report · laya · test

## Run header

- model: `convaiinnovations/laya/multilingual` @ `85cc74ddae6109077ebe2853a9b3077fb6606a78`
- dtype fp16 · device Tesla T4 · latency mode in_process
- libraries: {'laya': '0.4.31', 'torch': '2.11.0+cu130', 'transformers': '5.20.2'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.649 · macro-F1 0.546

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.856 | 0.696 | 0.768 | 444 |
| out_of_scope | 0.255 | 0.411 | 0.315 | 95 |
| quick_reply | 0.468 | 0.685 | 0.556 | 54 |

### feature_classification

n = 593 · accuracy 0.337 · macro-F1 0.349

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.156 | 0.364 | 0.219 | 77 |
| product_policy_analysis | 0.272 | 0.329 | 0.298 | 140 |
| comparison | 0.688 | 0.138 | 0.229 | 80 |
| ibip_screening | 0.253 | 0.297 | 0.273 | 74 |
| client_drafting | 0.692 | 0.616 | 0.652 | 73 |
| none | 0.623 | 0.322 | 0.425 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.523 · macro-F1 0.378

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.522 | 0.965 | 0.678 | 231 |
| complex | 0.529 | 0.042 | 0.078 | 213 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.415 · macro-F1 0.421

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.449 | 0.587 | 0.509 | 201 |
| agentic | 0.531 | 0.214 | 0.305 | 243 |
| refuse | 0.255 | 0.411 | 0.315 | 95 |
| quick_reply | 0.468 | 0.685 | 0.556 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 208 |
| feature_classification | 120 |
| complexity_estimation | 19 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.411 |
| safety_leak | 35 | 0.571 |
| non_leak | 60 | 0.317 |
| leak: data_extraction | 5 | 0.800 |
| leak: fraud_or_illegal | 5 | 0.600 |
| leak: jailbreak | 4 | 1.000 |
| leak: prompt_injection | 18 | 0.389 |
| leak: social_engineering_or_abuse | 3 | 0.667 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.117 | 0.489 |
| feature_classification | 593 | 0.409 | 1.017 |
| complexity_estimation | 444 | 0.326 | 0.699 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 550.6 | 526 | 727 | 326480 |
| input_ref | 593 | 389.3 | 381 | 446 | 230854 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 32.5 | 31.7 | 37.5 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 321908995, 'params_method': 'sum of numel over agent.model.parameters() (encoder + decision head)', 'disk_mb': 678.2, 'peak_gpu_mem_mb': 1532.0, 'peak_host_ram_mb': 2958.6}
