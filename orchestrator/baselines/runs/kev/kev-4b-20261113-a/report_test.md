# Report · kev · test

## Run header

- model: `jaredpalmer/kev-4b` @ `139fdd94f1b6a6ad80cc15e08fcb99cac885a101:139fdd94f1b6a6ad80cc15e08fcb99cac885a101`
- dtype bfloat16 · device Tesla T4 · latency mode in_process
- libraries: {'torch': '2.8.0+cu128', 'kev': '2074cc44256200bb37540103fa4572901faa10f3'}
- rows 593 · error rows 0 · truncated 0
- dispatcher oracle (gold fields): 593/593

## Quality

### scope_check

n = 593 · accuracy 0.801 · macro-F1 0.773

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| in_scope | 0.937 | 0.804 | 0.865 | 444 |
| out_of_scope | 0.444 | 0.789 | 0.568 | 95 |
| quick_reply | 1.000 | 0.796 | 0.887 | 54 |

### feature_classification

n = 593 · accuracy 0.801 · macro-F1 0.810

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| regulatory_consultation | 0.833 | 0.584 | 0.687 | 77 |
| product_policy_analysis | 0.689 | 0.886 | 0.775 | 140 |
| comparison | 0.961 | 0.613 | 0.748 | 80 |
| ibip_screening | 0.986 | 0.932 | 0.958 | 74 |
| client_drafting | 0.969 | 0.863 | 0.913 | 73 |
| none | 0.723 | 0.839 | 0.776 | 149 |

### complexity_estimation (gold in_scope rows)

n = 444 · accuracy 0.822 · macro-F1 0.821

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| simple | 0.937 | 0.706 | 0.805 | 231 |
| complex | 0.748 | 0.948 | 0.836 | 213 |

### needs_clarification (gold in_scope rows; positive = needs clarification)

n = 444 · accuracy 0.383 · macro-F1 0.382

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| True | 0.233 | 0.735 | 0.354 | 102 |
| False | 0.779 | 0.278 | 0.409 | 342 |

### route, end-to-end (tau=None)

n = 593 · accuracy 0.423 · macro-F1 0.471

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| lightweight | 0.800 | 0.044 | 0.083 | 183 |
| agentic | 0.644 | 0.365 | 0.466 | 159 |
| clarification | 0.238 | 0.657 | 0.350 | 102 |
| refuse | 0.444 | 0.789 | 0.568 | 95 |
| quick_reply | 1.000 | 0.796 | 0.887 | 54 |

### Route attribution (first wrong field for each wrong route)

| first wrong | n |
|---|---|
| needs_clarification | 183 |
| scope_check | 118 |
| feature_classification | 40 |
| complexity_estimation | 1 |

## Refusal recall

| slice | gold refuse | recall |
|---|---|---|
| all | 95 | 0.789 |
| safety_leak | 35 | 0.771 |
| non_leak | 60 | 0.800 |
| leak: data_extraction | 5 | 1.000 |
| leak: fraud_or_illegal | 5 | 1.000 |
| leak: jailbreak | 4 | 1.000 |
| leak: prompt_injection | 18 | 0.556 |
| leak: social_engineering_or_abuse | 3 | 1.000 |

## Calibration (probabilities as shipped, 10 bins)

| question | n | ECE | Brier |
|---|---|---|---|
| scope_check | 593 | 0.150 | 0.320 |
| feature_classification | 593 | 0.197 | 0.350 |
| complexity_estimation | 444 | 0.131 | 0.299 |
| slots (pooled, where gold slot status exists) | 1149 | 0.181 | 0.750 |

## Tokens, latency, size

| quantity | n | mean | median | p95 | total |
|---|---|---|---|---|---|
| input_native | 593 | 605.1 | 659 | 846 | 358806 |
| input_ref | 593 | 560.0 | 601 | 743 | 332106 |
| output_native | 0 | n/a | n/a | n/a | n/a |
| latency_ms | 583 | 3639.5 | 3825.9 | 4706.4 | |

Warm-up rows excluded from latency: 10.

Model size: {'params_total': 4207062528, 'params_method': 'sum(p.numel()) over the loaded DecisionModel (base + merged LoRA + pointer head)', 'disk_mb_adapter': 159.7, 'disk_mb_base': None, 'disk_mb': 159.7, 'peak_gpu_mem_mb': 8936.9, 'peak_host_ram_mb': None}
