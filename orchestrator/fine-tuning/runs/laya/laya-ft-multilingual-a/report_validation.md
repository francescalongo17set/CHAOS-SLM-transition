# Report · laya · validation

## Run header

- model: `convaiinnovations/laya/multilingual fine-tuned (laya-ft-multilingual-a)` @ `ft:d0f3f358744a4a5c`
- dtype fp16 · device Tesla T4 · latency mode in_process
- libraries: {'laya': '0.4.31', 'torch': '2.11.0+cu130', 'transformers': '5.20.2'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.946 · macro-F1 0.918

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.964 | 0.969 | 0.967 | 224 |
| out_of_scope | 0.857 | 0.875 | 0.866 | 48 |
| quick_reply | 0.958 | 0.885 | 0.920 | 26 |

### feature_classification

n = 298 · accuracy 0.933 · macro-F1 0.937

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.833 | 0.897 | 0.864 | 39 |
| product_policy_analysis | 0.918 | 0.944 | 0.931 | 71 |
| comparison | 0.974 | 0.950 | 0.962 | 40 |
| ibip_screening | 1.000 | 0.973 | 0.986 | 37 |
| client_drafting | 0.972 | 0.946 | 0.959 | 37 |
| none | 0.931 | 0.905 | 0.918 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.915 · macro-F1 0.915

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.900 | 0.939 | 0.919 | 115 |
| complex | 0.933 | 0.890 | 0.911 | 109 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.930 · macro-F1 0.918

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.898 | 0.960 | 0.928 | 101 |
| agentic | 0.983 | 0.935 | 0.958 | 123 |
| refuse | 0.857 | 0.875 | 0.866 | 48 |
| quick_reply | 0.958 | 0.885 | 0.920 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 16 |
| complexity_estimation | 4 |
| feature_classification | 1 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.875 |
| safety_leak | 18 | 0.722 |
| non_leak | 30 | 0.967 |
| leak: data_extraction | 2 | 1.000 |
| leak: fraud_or_illegal | 3 | 0.333 |
| leak: jailbreak | 2 | 1.000 |
| leak: prompt_injection | 9 | 0.667 |
| leak: social_engineering_or_abuse | 2 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.023 | 0.088 |
| feature_classification | 298 | 0.015 | 0.106 |
| complexity_estimation | 224 | 0.046 | 0.127 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 572.0 | 539.5 | 766 | 170470 |
| input_ref | 298 | 392.4 | 381.5 | 454 | 116946 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 32.7 | 32.0 | 37.8 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 321908995, 'params_method': 'sum of numel over agent.model.parameters() (encoder + decision head)', 'disk_mb': 678.2, 'peak_gpu_mem_mb': 1532.0, 'peak_host_ram_mb': 2888.3}
