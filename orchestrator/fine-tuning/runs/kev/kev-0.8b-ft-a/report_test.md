# Report · kev · test

## Run header

- model: `/kaggle/working/runs/kev/kev-0.8b-ft-a/checkpoint` @ `checkpoint`
- dtype float32 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.922 · macro-F1 0.885

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.924 | 0.980 | 0.951 | 444 |
| out_of_scope | 0.870 | 0.632 | 0.732 | 95 |
| quick_reply | 0.981 | 0.963 | 0.972 | 54 |

### feature_classification

n = 593 · accuracy 0.874 · macro-F1 0.878

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.713 | 0.870 | 0.784 | 77 |
| product_policy_analysis | 0.854 | 0.879 | 0.866 | 140 |
| comparison | 0.932 | 0.863 | 0.896 | 80 |
| ibip_screening | 0.957 | 0.892 | 0.923 | 74 |
| client_drafting | 0.957 | 0.904 | 0.930 | 73 |
| none | 0.888 | 0.852 | 0.870 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.883 · macro-F1 0.882

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.874 | 0.905 | 0.889 | 231 |
| complex | 0.893 | 0.859 | 0.876 | 213 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.882 · macro-F1 0.874

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.808 | 0.940 | 0.869 | 201 |
| agentic | 0.937 | 0.914 | 0.925 | 243 |
| refuse | 0.870 | 0.632 | 0.732 | 95 |
| quick_reply | 0.981 | 0.963 | 0.972 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 46 |
| complexity_estimation | 15 |
| feature_classification | 9 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.632 |
| safety_leak | 35 | 0.600 |
| non_leak | 60 | 0.650 |
| leak: data_extraction | 5 | 0.600 |
| leak: fraud_or_illegal | 5 | 0.400 |
| leak: jailbreak | 4 | 0.750 |
| leak: prompt_injection | 18 | 0.556 |
| leak: social_engineering_or_abuse | 3 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.030 | 0.111 |
| feature_classification | 593 | 0.021 | 0.190 |
| complexity_estimation | 444 | 0.018 | 0.178 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 381.3 | 373 | 438 | 226110 |
| input_ref | 593 | 389.3 | 381 | 446 | 230854 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 248.2 | 247.9 | 264.3 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 65.5, 'disk_mb_base': 1769.9, 'disk_mb': 1835.4, 'peak_gpu_mem_mb': 3460.0, 'peak_gpu_mem_mb_per_device': None, 'layer_split': None, 'peak_host_ram_mb': None}
