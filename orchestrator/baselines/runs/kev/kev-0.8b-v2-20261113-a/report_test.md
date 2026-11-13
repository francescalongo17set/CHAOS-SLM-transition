# Report · kev · test

## Run header

- model: `jaredpalmer/kev-0.8b` @ `9a45d25eb2ab761841196625383fa1dff0e56c1e:9a45d25eb2ab761841196625383fa1dff0e56c1e`
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

### route, end-to-end (tau=None)

n = 593 · accuracy 0.654 · macro-F1 0.550

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.636 | 0.697 | 0.665 | 201 |
| agentic | 0.741 | 0.802 | 0.771 | 243 |
| refuse | 0.923 | 0.126 | 0.222 | 95 |
| quick_reply | 0.423 | 0.759 | 0.543 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 126 |
| feature_classification | 49 |
| complexity_estimation | 30 |

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

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 381.3 | 373 | 438 | 226110 |
| input_ref | 593 | 389.3 | 381 | 446 | 230854 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 286.1 | 283.0 | 311.6 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 65.5, 'disk_mb_base': 1769.9, 'disk_mb': 1835.4, 'peak_gpu_mem_mb': 3217.3, 'peak_gpu_mem_mb_per_device': None, 'layer_split': None, 'peak_host_ram_mb': None}
