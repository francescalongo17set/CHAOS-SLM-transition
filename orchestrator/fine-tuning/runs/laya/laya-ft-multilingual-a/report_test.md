# Report · laya · test

## Run header

- model: `convaiinnovations/laya/multilingual fine-tuned (laya-ft-multilingual-a)` @ `ft:d0f3f358744a4a5c`
- dtype fp16 · device Tesla T4 · latency mode in_process
- libraries: {'laya': '0.4.31', 'torch': '2.11.0+cu130', 'transformers': '5.20.2'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.960 · macro-F1 0.936

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.971 | 0.984 | 0.978 | 444 |
| out_of_scope | 0.900 | 0.853 | 0.876 | 95 |
| quick_reply | 0.962 | 0.944 | 0.953 | 54 |

### feature_classification

n = 593 · accuracy 0.889 · macro-F1 0.891

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.815 | 0.857 | 0.835 | 77 |
| product_policy_analysis | 0.827 | 0.886 | 0.855 | 140 |
| comparison | 0.971 | 0.825 | 0.892 | 80 |
| ibip_screening | 0.985 | 0.865 | 0.921 | 74 |
| client_drafting | 0.899 | 0.973 | 0.934 | 73 |
| none | 0.907 | 0.913 | 0.910 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.881 · macro-F1 0.880

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.880 | 0.892 | 0.886 | 231 |
| complex | 0.881 | 0.869 | 0.875 | 213 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.916 · macro-F1 0.916

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.860 | 0.945 | 0.900 | 201 |
| agentic | 0.965 | 0.909 | 0.936 | 243 |
| refuse | 0.900 | 0.853 | 0.876 | 95 |
| quick_reply | 0.962 | 0.944 | 0.953 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 24 |
| complexity_estimation | 18 |
| feature_classification | 8 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.853 |
| safety_leak | 35 | 0.914 |
| non_leak | 60 | 0.817 |
| leak: data_extraction | 5 | 0.800 |
| leak: fraud_or_illegal | 5 | 0.800 |
| leak: jailbreak | 4 | 1.000 |
| leak: prompt_injection | 18 | 1.000 |
| leak: social_engineering_or_abuse | 3 | 0.667 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.019 | 0.074 |
| feature_classification | 593 | 0.031 | 0.175 |
| complexity_estimation | 444 | 0.084 | 0.191 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 550.6 | 526 | 727 | 326480 |
| input_ref | 593 | 389.3 | 381 | 446 | 230854 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 32.5 | 32.1 | 36.0 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 321908995, 'params_method': 'sum of numel over agent.model.parameters() (encoder + decision head)', 'disk_mb': 678.2, 'peak_gpu_mem_mb': 1529.5, 'peak_host_ram_mb': 2890.0}
