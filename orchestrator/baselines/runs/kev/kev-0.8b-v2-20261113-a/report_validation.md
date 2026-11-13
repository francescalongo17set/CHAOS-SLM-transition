# Report · kev · validation

## Run header

- model: `jaredpalmer/kev-0.8b` @ `9a45d25eb2ab761841196625383fa1dff0e56c1e:9a45d25eb2ab761841196625383fa1dff0e56c1e`
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

### route, end-to-end (tau=None)

n = 298 · accuracy 0.678 · macro-F1 0.596

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.655 | 0.772 | 0.709 | 101 |
| agentic | 0.841 | 0.732 | 0.783 | 123 |
| refuse | 0.769 | 0.208 | 0.328 | 48 |
| quick_reply | 0.407 | 0.923 | 0.565 | 26 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| scope_check | 60 |
| feature_classification | 26 |
| complexity_estimation | 10 |

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

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 298 | 384.4 | 373.5 | 446 | 114562 |
| input_ref | 298 | 392.4 | 381.5 | 454 | 116946 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 288 | 276.5 | 275.1 | 305.5 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 752917824, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 65.5, 'disk_mb_base': 1769.9, 'disk_mb': 1835.4, 'peak_gpu_mem_mb': 3217.3, 'peak_gpu_mem_mb_per_device': None, 'layer_split': None, 'peak_host_ram_mb': None}
