# Report · kev · validation

## Run header

- model: `jaredpalmer/kev-4b` @ `139fdd94f1b6a6ad80cc15e08fcb99cac885a101:139fdd94f1b6a6ad80cc15e08fcb99cac885a101`
- dtype bfloat16 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.792 · macro-F1 0.784

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.955 | 0.759 | 0.846 | 224 |
| out_of_scope | 0.455 | 0.938 | 0.612 | 48 |
| quick_reply | 1.000 | 0.808 | 0.894 | 26 |

### feature_classification

n = 298 · accuracy 0.775 · macro-F1 0.778

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.783 | 0.462 | 0.581 | 39 |
| product_policy_analysis | 0.726 | 0.859 | 0.787 | 71 |
| comparison | 1.000 | 0.825 | 0.904 | 40 |
| ibip_screening | 1.000 | 0.730 | 0.844 | 37 |
| client_drafting | 0.853 | 0.784 | 0.817 | 37 |
| none | 0.649 | 0.851 | 0.737 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.812 · macro-F1 0.812

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.869 | 0.748 | 0.804 | 115 |
| complex | 0.768 | 0.881 | 0.821 | 109 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 224 · accuracy 0.384 · macro-F1 0.382

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.225 | 0.720 | 0.343 | 50 |
| False | 0.781 | 0.287 | 0.420 | 174 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.436 · macro-F1 0.483

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.500 | 0.065 | 0.115 | 92 |
| agentic | 0.735 | 0.305 | 0.431 | 82 |
| clarification | 0.250 | 0.660 | 0.363 | 50 |
| refuse | 0.455 | 0.938 | 0.612 | 48 |
| quick_reply | 1.000 | 0.808 | 0.894 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 86 |
| scope_check | 62 |
| feature_classification | 20 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.938 |
| safety_leak | 18 | 0.889 |
| non_leak | 30 | 0.967 |
| leak: data_extraction | 2 | 1.000 |
| leak: fraud_or_illegal | 3 | 0.667 |
| leak: jailbreak | 2 | 1.000 |
| leak: prompt_injection | 9 | 0.889 |
| leak: social_engineering_or_abuse | 2 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.147 | 0.313 |
| feature_classification | 298 | 0.186 | 0.340 |
| complexity_estimation | 224 | 0.125 | 0.307 |
| slots (pooled, where gold slot status exists) | 554 | 0.255 | 0.845 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 605.0 | 667.0 | 862 | 180299 |
| input_ref | 298 | 559.9 | 605.0 | 751 | 166837 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 3591.2 | 3832.4 | 5050.6 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 4207062528, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 159.7, 'disk_mb_base': None, 'disk_mb': 159.7, 'peak_gpu_mem_mb': 8936.9, 'peak_host_ram_mb': None}
