# Report · kev · validation

## Run header

- model: `jaredpalmer/kev-9b` @ `b5d8c18e44c60888d138b65cb6507ff0a5a448a0:b5d8c18e44c60888d138b65cb6507ff0a5a448a0`
- dtype bfloat16 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.842 · macro-F1 0.818

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.954 | 0.839 | 0.893 | 224 |
| out_of_scope | 0.519 | 0.854 | 0.646 | 48 |
| quick_reply | 1.000 | 0.846 | 0.917 | 26 |

### feature_classification

n = 298 · accuracy 0.832 · macro-F1 0.849

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.897 | 0.667 | 0.765 | 39 |
| product_policy_analysis | 0.838 | 0.803 | 0.820 | 71 |
| comparison | 1.000 | 0.925 | 0.961 | 40 |
| ibip_screening | 1.000 | 0.838 | 0.912 | 37 |
| client_drafting | 0.912 | 0.838 | 0.873 | 37 |
| none | 0.667 | 0.892 | 0.763 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.804 · macro-F1 0.804

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.820 | 0.791 | 0.805 | 115 |
| complex | 0.788 | 0.817 | 0.802 | 109 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 224 · accuracy 0.460 · macro-F1 0.443

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.237 | 0.640 | 0.346 | 50 |
| False | 0.798 | 0.408 | 0.540 | 174 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.473 · macro-F1 0.534

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.750 | 0.163 | 0.268 | 92 |
| agentic | 0.667 | 0.439 | 0.529 | 82 |
| clarification | 0.220 | 0.540 | 0.312 | 50 |
| refuse | 0.519 | 0.854 | 0.646 | 48 |
| quick_reply | 1.000 | 0.846 | 0.917 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 94 |
| scope_check | 47 |
| feature_classification | 16 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.854 |
| safety_leak | 18 | 0.667 |
| non_leak | 30 | 0.967 |
| leak: data_extraction | 2 | 1.000 |
| leak: fraud_or_illegal | 3 | 0.667 |
| leak: jailbreak | 2 | 1.000 |
| leak: prompt_injection | 9 | 0.556 |
| leak: social_engineering_or_abuse | 2 | 0.500 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.152 | 0.263 |
| feature_classification | 298 | 0.110 | 0.259 |
| complexity_estimation | 224 | 0.054 | 0.282 |
| slots (pooled, where gold slot status exists) | 561 | 0.044 | 0.472 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 595.5 | 641.5 | 852 | 177466 |
| input_ref | 298 | 551.0 | 583.0 | 746 | 164199 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 5700.8 | 6042.5 | 7791.4 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 7938782208, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 201.7, 'disk_mb_base': None, 'disk_mb': 201.7, 'peak_gpu_mem_mb': 16338.5, 'peak_gpu_mem_mb_per_device': [13622.5, 2716.0], 'layer_split': {'embed_tokens': '0', 'layers.0': '0', 'layers.1': '0', 'layers.2': '0', 'layers.3': '0', 'layers.4': '0', 'layers.5': '0', 'layers.6': '0', 'layers.7': '0', 'layers.8': '0', 'layers.9': '0', 'layers.10': '0', 'layers.11': '0', 'layers.12': '0', 'layers.13': '0', 'layers.14': '0', 'layers.15': '0', 'layers.16': '0', 'layers.17': '0', 'layers.18': '0', 'layers.19': '0', 'layers.20': '0', 'layers.21': '0', 'layers.22': '0', 'layers.23': '0', 'layers.24': '0', 'layers.25': '0', 'layers.26': '1', 'layers.27': '1', 'layers.28': '1', 'layers.29': '1', 'layers.30': '1', 'layers.31': '1', 'norm': '1', 'rotary_emb': '1'}, 'peak_host_ram_mb': None}
