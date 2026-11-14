# Report · kev · validation

## Run header

- model: `/kaggle/working/runs/kev/kev-0.8b-ft-a/checkpoint` @ `checkpoint`
- dtype float32 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.930 · macro-F1 0.904

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.947 | 0.960 | 0.953 | 224 |
| out_of_scope | 0.809 | 0.792 | 0.800 | 48 |
| quick_reply | 1.000 | 0.923 | 0.960 | 26 |

### feature_classification

n = 298 · accuracy 0.876 · macro-F1 0.880

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.745 | 0.897 | 0.814 | 39 |
| product_policy_analysis | 0.901 | 0.901 | 0.901 | 71 |
| comparison | 0.973 | 0.900 | 0.935 | 40 |
| ibip_screening | 0.947 | 0.973 | 0.960 | 37 |
| client_drafting | 0.906 | 0.784 | 0.841 | 37 |
| none | 0.836 | 0.824 | 0.830 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.888 · macro-F1 0.888

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.888 | 0.896 | 0.892 | 115 |
| complex | 0.889 | 0.881 | 0.885 | 109 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.889 · macro-F1 0.889

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.836 | 0.911 | 0.872 | 101 |
| agentic | 0.949 | 0.902 | 0.925 | 123 |
| refuse | 0.809 | 0.792 | 0.800 | 48 |
| quick_reply | 1.000 | 0.923 | 0.960 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 21 |
| feature_classification | 9 |
| complexity_estimation | 3 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.792 |
| safety_leak | 18 | 0.611 |
| non_leak | 30 | 0.900 |
| leak: data_extraction | 2 | 0.500 |
| leak: fraud_or_illegal | 3 | 0.000 |
| leak: jailbreak | 2 | 1.000 |
| leak: prompt_injection | 9 | 0.667 |
| leak: social_engineering_or_abuse | 2 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.016 | 0.102 |
| feature_classification | 298 | 0.058 | 0.186 |
| complexity_estimation | 224 | 0.019 | 0.170 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 384.4 | 373.5 | 446 | 114562 |
| input_ref | 298 | 392.4 | 381.5 | 454 | 116946 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 279.4 | 276.4 | 306.5 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 65.5, 'disk_mb_base': 1769.9, 'disk_mb': 1835.4, 'peak_gpu_mem_mb': 3465.4, 'peak_gpu_mem_mb_per_device': None, 'layer_split': None, 'peak_host_ram_mb': None}
