# Paired SARI analysis

Delta = SARI(ablated) - SARI(original), computed before rounding.

| Dataset | Prompt | Original | Ablated | Delta | 95% CI | p | Holm p |
|---|---|---:|---:|---:|---|---:|---:|
| cochrane | iso | 38.40 | 38.44 | +0.047 | [-0.484, 0.573] | 0.86185 | 1.00000 |
| cochrane | iso_examples | 38.09 | 38.06 | -0.032 | [-0.444, 0.392] | 0.88490 | 1.00000 |
| plaba | iso | 36.30 | 36.37 | +0.075 | [-0.512, 0.654] | 0.80155 | 1.00000 |
| plaba | iso_examples | 36.68 | 36.57 | -0.102 | [-0.602, 0.412] | 0.69450 | 1.00000 |
| tsar2025 | iso | 46.68 | 46.93 | +0.254 | [-0.573, 1.092] | 0.54790 | 1.00000 |
| tsar2025 | iso_examples | 47.18 | 47.07 | -0.110 | [-0.877, 0.623] | 0.77625 | 1.00000 |

## Method

10,000 paired item bootstrap replicates; percentile 95% intervals. Two-sided within-item randomization tests with 19,999 swaps and the (extreme + 1)/(B + 1) correction. Holm adjustment across six comparisons. Seed 42, independent deterministic streams. All outputs, including truncations, retained.

The installed standard SARI corpus implementation was inspected and executed on both conditions for every replicate. Only its deterministic normalization and sentence-level kernel calls were cached. Full scores were checked against the public metric API and the completed evaluation. Unrounded values were used throughout inference. The displayed delta may differ from subtracting the separately rounded displayed scores.

## Observations

All six confidence intervals include zero. None of the six tests rejects the paired exchangeability null at 0.05, either before or after Holm adjustment. These data do not show a detectable SARI change from removing the specified organization/summary block.

## Limits

This is not evidence of equivalence or absence of structural effects. SARI does not directly measure summary-first organization, information hierarchy or ISO compliance. The analysis is conditional on the single deterministic model runs and test sets, with no inference about demonstration seeds or other models. Remaining differences in prompt length, instruction count, omission permissions and retained structural requirements prevent attributing a complete causal effect to ISO 24495-1.

The resampling unit is a test row. PLABA has repeated text IDs; within-document dependence is not modeled by this item-level analysis. Confidence intervals are pointwise, not simultaneous. Qualitative inspection and the full scientific report remain separate steps.
