# Plan assertions (book 16.5)

| check | result | detail |
| --- | --- | --- |
| quota ('product_policy_analysis', 'simple') lightweight | PASS |  |
| quota ('product_policy_analysis', 'simple') clarification | PASS |  |
| quota ('product_policy_analysis', 'complex') clarification | PASS |  |
| quota ('product_policy_analysis', 'complex') agentic | PASS |  |
| quota ('comparison', 'simple') lightweight | PASS |  |
| quota ('comparison', 'simple') clarification | PASS |  |
| quota ('comparison', 'complex') clarification | PASS |  |
| quota ('comparison', 'complex') agentic | PASS |  |
| quota ('regulatory_consultation', 'simple') lightweight | PASS |  |
| quota ('regulatory_consultation', 'simple') clarification | PASS |  |
| quota ('regulatory_consultation', 'complex') clarification | PASS |  |
| quota ('regulatory_consultation', 'complex') agentic | PASS |  |
| quota ('client_drafting', 'simple') clarification | PASS |  |
| quota ('client_drafting', 'simple') agentic | PASS |  |
| quota ('client_drafting', 'complex') clarification | PASS |  |
| quota ('client_drafting', 'complex') agentic | PASS |  |
| quota ('ibip_screening', 'simple') clarification | PASS |  |
| quota ('ibip_screening', 'simple') agentic | PASS |  |
| quota ('ibip_screening', 'complex') clarification | PASS |  |
| quota ('ibip_screening', 'complex') agentic | PASS |  |
| split ('product_policy_analysis', 'simple') train | PASS |  |
| split ('product_policy_analysis', 'simple') validation | PASS |  |
| split ('product_policy_analysis', 'simple') test | PASS |  |
| split ('product_policy_analysis', 'complex') train | PASS |  |
| split ('product_policy_analysis', 'complex') validation | PASS |  |
| split ('product_policy_analysis', 'complex') test | PASS |  |
| split ('comparison', 'simple') train | PASS |  |
| split ('comparison', 'simple') validation | PASS |  |
| split ('comparison', 'simple') test | PASS |  |
| split ('comparison', 'complex') train | PASS |  |
| split ('comparison', 'complex') validation | PASS |  |
| split ('comparison', 'complex') test | PASS |  |
| split ('regulatory_consultation', 'simple') train | PASS |  |
| split ('regulatory_consultation', 'simple') validation | PASS |  |
| split ('regulatory_consultation', 'simple') test | PASS |  |
| split ('regulatory_consultation', 'complex') train | PASS |  |
| split ('regulatory_consultation', 'complex') validation | PASS |  |
| split ('regulatory_consultation', 'complex') test | PASS |  |
| split ('client_drafting', 'simple') train | PASS |  |
| split ('client_drafting', 'simple') validation | PASS |  |
| split ('client_drafting', 'simple') test | PASS |  |
| split ('client_drafting', 'complex') train | PASS |  |
| split ('client_drafting', 'complex') validation | PASS |  |
| split ('client_drafting', 'complex') test | PASS |  |
| split ('ibip_screening', 'simple') train | PASS |  |
| split ('ibip_screening', 'simple') validation | PASS |  |
| split ('ibip_screening', 'simple') test | PASS |  |
| split ('ibip_screening', 'complex') train | PASS |  |
| split ('ibip_screening', 'complex') validation | PASS |  |
| split ('ibip_screening', 'complex') test | PASS |  |
| route mix | PASS | Counter({'lightweight': 930, 'agentic': 810, 'clarification': 510, 'refuse': 480, 'quick_reply': 270}) |
| scenario totals | PASS |  |
| modifier totals | PASS | {'context_conflict': 120, 'mixed_features': 150, 'innocent_imperative': 60, 'negation_or_exception': 150, 'long_preamble': 180, 'telegraphic': 240, 'c |
| style totals | PASS |  |
| pair examples | PASS | 900 |
| ids unique | PASS |  |
| record counts | PASS | router 3000 qa 1500 |
| test isolation | PASS | [] |
| held-out sections | PASS | [] |
| families in one split | PASS | {} |
| pairs in one job | PASS |  |
| held-out leak families | PASS |  |
| QA caps | PASS | [] |
| router-only caps | PASS | [] |
| labels and dispatcher | PASS |  |
| pair members: same style, no length-changing modifier | PASS |  |
| telegraphic never with preamble or mixed features | PASS |  |
| absent topics | PASS | 5 |
| section spread | PASS | [] |