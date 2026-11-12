# Diversity check

All router: {'n': 2983, 'top_first_word': 'e', 'top_share': 0.064, 'dup_rate': 0.0, 'len_mean': 14.9, 'len_min': 2, 'len_max': 60, 'first3_distinct': 0.648}

All QA: {'n': 1485, 'top_first_word': 'zurich', 'top_share': 0.227, 'dup_rate': 0.0, 'len_mean': 18.8, 'len_min': 5, 'len_max': 42, 'first3_distinct': 0.591}

| cell | n | top first word | share | dup | mean words | min-max | flag (>5%) |
|---|---|---|---|---|---|---|---|
| qa/absent/absent | 297 | zurich | 0.195 | 0.0 | 15.7 | 5-25 | YES |
| qa/conditional/answer | 369 | zurich | 0.247 | 0.0 | 20.7 | 5-40 | YES |
| qa/multi_fact/answer | 224 | zurich | 0.223 | 0.0 | 25.6 | 5-42 | YES |
| qa/single_value/answer | 595 | zurich | 0.232 | 0.0 | 16.7 | 5-36 | YES |
| router/client_drafting/agentic | 227 | scrivi | 0.322 | 0.0 | 18.9 | 4-50 | YES |
| router/client_drafting/clarification | 142 | scrivi | 0.303 | 0.0 | 18.3 | 3-52 | YES |
| router/comparison/agentic | 256 | zurich | 0.191 | 0.0 | 15.7 | 4-43 | YES |
| router/comparison/clarification | 82 | ma | 0.085 | 0.0 | 13.6 | 3-38 | YES |
| router/comparison/lightweight | 60 | e | 0.2 | 0.0 | 14.6 | 3-43 | YES |
| router/ibip_screening/agentic | 218 | italiana | 0.142 | 0.0 | 24.6 | 3-53 | YES |
| router/ibip_screening/clarification | 152 | italiana | 0.184 | 0.0 | 18.2 | 3-45 | YES |
| router/none/quick_reply | 268 | ok | 0.082 | 0.0 | 4.8 | 2-9 | YES |
| router/none/refuse | 478 | mi | 0.092 | 0.0 | 14.7 | 3-42 | YES |
| router/product_policy_analysis/agentic | 59 | ok | 0.136 | 0.0 | 24.9 | 3-60 | YES |
| router/product_policy_analysis/clarification | 98 | per | 0.082 | 0.0 | 13.4 | 3-49 | YES |
| router/product_policy_analysis/lightweight | 554 | e | 0.148 | 0.0 | 12.3 | 3-47 | YES |
| router/regulatory_consultation/agentic | 46 | se | 0.239 | 0.0 | 23.1 | 11-38 | YES |
| router/regulatory_consultation/clarification | 34 | se | 0.147 | 0.0 | 14.1 | 3-32 | YES |
| router/regulatory_consultation/lightweight | 309 | quali | 0.113 | 0.0 | 12.4 | 4-34 | YES |