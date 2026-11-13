# Report · kev · validation

## Run header

- model: `jaredpalmer/kev-0.8b` @ `v1.0:bf75a6a8848ea6960ff2ed108d9ed44c2941174f`
- dtype float32 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 298 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 298/298

## Quality

### scope_check

n = 298 · accuracy 0.799 · macro-F1 0.600

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.903 | 0.911 | 0.907 | 224 |
| out_of_scope | 0.769 | 0.208 | 0.328 | 48 |
| quick_reply | 0.407 | 0.923 | 0.565 | 26 |

### feature_classification

n = 298 · accuracy 0.664 · macro-F1 0.672

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.917 | 0.282 | 0.431 | 39 |
| product_policy_analysis | 0.657 | 0.620 | 0.638 | 71 |
| comparison | 0.941 | 0.800 | 0.865 | 40 |
| ibip_screening | 1.000 | 0.676 | 0.806 | 37 |
| client_drafting | 0.719 | 0.622 | 0.667 | 37 |
| none | 0.492 | 0.851 | 0.624 | 74 |

### complexity_estimation (gold in_scope rows)

n = 224 · accuracy 0.772 · macro-F1 0.771

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.750 | 0.835 | 0.790 | 115 |
| complex | 0.802 | 0.706 | 0.751 | 109 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 224 · accuracy 0.415 · macro-F1 0.410

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.235 | 0.720 | 0.355 | 50 |
| False | 0.803 | 0.328 | 0.465 | 174 |

### route, end-to-end (tau=None)

n = 298 · accuracy 0.349 · macro-F1 0.357

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.510 | 0.283 | 0.364 | 92 |
| agentic | 0.417 | 0.122 | 0.189 | 82 |
| clarification | 0.225 | 0.680 | 0.338 | 50 |
| refuse | 0.769 | 0.208 | 0.328 | 48 |
| quick_reply | 0.407 | 0.923 | 0.565 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 98 |
| scope_check | 60 |
| feature_classification | 36 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 48 | 0.208 |
| safety_leak | 18 | 0.056 |
| non_leak | 30 | 0.300 |
| leak: data_extraction | 2 | 0.000 |
| leak: fraud_or_illegal | 3 | 0.000 |
| leak: jailbreak | 2 | 0.000 |
| leak: prompt_injection | 9 | 0.000 |
| leak: social_engineering_or_abuse | 2 | 0.500 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 298 | 0.281 | 0.427 |
| feature_classification | 298 | 0.195 | 0.508 |
| complexity_estimation | 224 | 0.146 | 0.367 |
| slots (pooled, where gold slot status exists) | 454 | 0.265 | 0.861 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 573.9 | 616.5 | 852 | 171017 |
| input_ref | 298 | 538.1 | 550.5 | 746 | 160344 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 430.1 | 466.2 | 587.8 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb': 65.5, 'peak_gpu_mem_mb': 3217.3, 'peak_host_ram_mb': None}
