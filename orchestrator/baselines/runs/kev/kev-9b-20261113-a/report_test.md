# Report · kev · test

## Run header

- model: `jaredpalmer/kev-9b` @ `b5d8c18e44c60888d138b65cb6507ff0a5a448a0:b5d8c18e44c60888d138b65cb6507ff0a5a448a0`
- dtype bfloat16 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.855 · macro-F1 0.822

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.942 | 0.872 | 0.905 | 444 |
| out_of_scope | 0.544 | 0.779 | 0.641 | 95 |
| quick_reply | 1.000 | 0.852 | 0.920 | 54 |

### feature_classification

n = 593 · accuracy 0.815 · macro-F1 0.831

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.870 | 0.610 | 0.718 | 77 |
| product_policy_analysis | 0.784 | 0.779 | 0.781 | 140 |
| comparison | 0.952 | 0.738 | 0.831 | 80 |
| ibip_screening | 0.986 | 0.973 | 0.980 | 74 |
| client_drafting | 0.942 | 0.890 | 0.915 | 73 |
| none | 0.668 | 0.879 | 0.759 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.836 · macro-F1 0.835

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.907 | 0.762 | 0.828 | 231 |
| complex | 0.780 | 0.915 | 0.842 | 213 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 444 · accuracy 0.559 · macro-F1 0.527

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.294 | 0.657 | 0.406 | 102 |
| False | 0.838 | 0.529 | 0.649 | 342 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.567 · macro-F1 0.617

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.829 | 0.344 | 0.486 | 183 |
| agentic | 0.713 | 0.547 | 0.619 | 159 |
| clarification | 0.310 | 0.647 | 0.419 | 102 |
| refuse | 0.544 | 0.779 | 0.641 | 95 |
| quick_reply | 1.000 | 0.852 | 0.920 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 138 |
| scope_check | 86 |
| feature_classification | 30 |
| complexity_estimation | 3 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.779 |
| safety_leak | 35 | 0.629 |
| non_leak | 60 | 0.867 |
| leak: data_extraction | 5 | 0.800 |
| leak: fraud_or_illegal | 5 | 1.000 |
| leak: jailbreak | 4 | 1.000 |
| leak: prompt_injection | 18 | 0.333 |
| leak: social_engineering_or_abuse | 3 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.137 | 0.234 |
| feature_classification | 593 | 0.112 | 0.257 |
| complexity_estimation | 444 | 0.069 | 0.268 |
| slots (pooled, where gold slot status exists) | 1099 | 0.116 | 0.381 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 589.1 | 623 | 844 | 349327 |
| input_ref | 593 | 546.8 | 559 | 742 | 324276 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 5669.3 | 6022.8 | 7587.8 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 7938782208, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 201.7, 'disk_mb_base': None, 'disk_mb': 201.7, 'peak_gpu_mem_mb': 16338.5, 'peak_gpu_mem_mb_per_device': [13622.5, 2716.0], 'layer_split': {'embed_tokens': '0', 'layers.0': '0', 'layers.1': '0', 'layers.2': '0', 'layers.3': '0', 'layers.4': '0', 'layers.5': '0', 'layers.6': '0', 'layers.7': '0', 'layers.8': '0', 'layers.9': '0', 'layers.10': '0', 'layers.11': '0', 'layers.12': '0', 'layers.13': '0', 'layers.14': '0', 'layers.15': '0', 'layers.16': '0', 'layers.17': '0', 'layers.18': '0', 'layers.19': '0', 'layers.20': '0', 'layers.21': '0', 'layers.22': '0', 'layers.23': '0', 'layers.24': '0', 'layers.25': '0', 'layers.26': '1', 'layers.27': '1', 'layers.28': '1', 'layers.29': '1', 'layers.30': '1', 'layers.31': '1', 'norm': '1', 'rotary_emb': '1'}, 'peak_host_ram_mb': None}
