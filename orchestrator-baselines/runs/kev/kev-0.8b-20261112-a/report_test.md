# Report · kev · test

## Run header

- model: `jaredpalmer/kev-0.8b` @ `v1.0:bf75a6a8848ea6960ff2ed108d9ed44c2941174f`
- dtype float32 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.788 · macro-F1 0.553

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.857 | 0.932 | 0.893 | 444 |
| out_of_scope | 0.923 | 0.126 | 0.222 | 95 |
| quick_reply | 0.423 | 0.759 | 0.543 | 54 |

### feature_classification

n = 593 · accuracy 0.663 · macro-F1 0.693

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.744 | 0.416 | 0.533 | 77 |
| product_policy_analysis | 0.677 | 0.479 | 0.561 | 140 |
| comparison | 0.869 | 0.662 | 0.752 | 80 |
| ibip_screening | 0.983 | 0.784 | 0.872 | 74 |
| client_drafting | 0.903 | 0.767 | 0.830 | 73 |
| none | 0.472 | 0.852 | 0.608 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.727 · macro-F1 0.726

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.727 | 0.762 | 0.744 | 231 |
| complex | 0.728 | 0.690 | 0.708 | 213 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 444 · accuracy 0.423 · macro-F1 0.415

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.234 | 0.667 | 0.347 | 102 |
| False | 0.779 | 0.351 | 0.484 | 342 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.331 · macro-F1 0.329

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.483 | 0.311 | 0.379 | 183 |
| agentic | 0.311 | 0.119 | 0.173 | 159 |
| clarification | 0.220 | 0.657 | 0.330 | 102 |
| refuse | 0.923 | 0.126 | 0.222 | 95 |
| quick_reply | 0.423 | 0.759 | 0.543 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 191 |
| scope_check | 126 |
| feature_classification | 80 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.126 |
| safety_leak | 35 | 0.057 |
| non_leak | 60 | 0.167 |
| leak: data_extraction | 5 | 0.000 |
| leak: fraud_or_illegal | 5 | 0.000 |
| leak: jailbreak | 4 | 0.500 |
| leak: prompt_injection | 18 | 0.000 |
| leak: social_engineering_or_abuse | 3 | 0.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.271 | 0.426 |
| feature_classification | 593 | 0.181 | 0.526 |
| complexity_estimation | 444 | 0.107 | 0.389 |
| slots (pooled, where gold slot status exists) | 860 | 0.275 | 0.862 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 552.2 | 541 | 836 | 327480 |
| input_ref | 593 | 517.7 | 469 | 738 | 307017 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 431.0 | 442.4 | 643.7 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb': 65.5, 'peak_gpu_mem_mb': 3217.3, 'peak_host_ram_mb': None}
