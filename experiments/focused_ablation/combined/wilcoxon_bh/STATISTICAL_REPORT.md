# Statistical analysis — current Wilcoxon/BH version

Main protocol: two-sided paired Wilcoxon signed-rank tests with BH FDR correction. Families were fixed before recalculation: 12 primary ablated-original contrasts and 12 secondary ablated-baseline contrasts. BH across all 24 is additionally reported. Earlier permutation/Holm results are retained as robustness evidence, not used as alternative favorable main tests.

## Primary: ablated minus original

| Model | Dataset | Prompt | Delta SARI | 95% CI | Wilcoxon p | BH q (family 12) | BH q (all 24) |
|---|---|---|---:|---|---:|---:|---:|
| Llama 3.1 8B | cochrane | iso | +0.047 | [-0.484, 0.573] | 0.85976 | 0.88992 | 0.88992 |
| Llama 3.1 8B | cochrane | iso_examples | -0.032 | [-0.444, 0.392] | 0.63266 | 0.85714 | 0.85714 |
| Llama 3.1 8B | plaba | iso | +0.075 | [-0.512, 0.654] | 0.54324 | 0.85714 | 0.85714 |
| Llama 3.1 8B | plaba | iso_examples | -0.102 | [-0.602, 0.412] | 0.68885 | 0.85714 | 0.85714 |
| Llama 3.1 8B | tsar2025 | iso | +0.254 | [-0.573, 1.092] | 0.71428 | 0.85714 | 0.85714 |
| Llama 3.1 8B | tsar2025 | iso_examples | -0.110 | [-0.877, 0.623] | 0.6368 | 0.85714 | 0.85714 |
| Mixtral 8x7B | cochrane | iso | +0.089 | [-0.621, 0.851] | 0.62148 | 0.85714 | 0.85714 |
| Mixtral 8x7B | cochrane | iso_examples | -0.022 | [-0.897, 0.828] | 0.88992 | 0.88992 | 0.88992 |
| Mixtral 8x7B | plaba | iso | +0.274 | [-0.736, 1.298] | 0.24642 | 0.85714 | 0.5914 |
| Mixtral 8x7B | plaba | iso_examples | +0.139 | [-0.885, 1.131] | 0.2155 | 0.85714 | 0.57467 |
| Mixtral 8x7B | tsar2025 | iso | +0.227 | [-0.974, 1.401] | 0.4671 | 0.85714 | 0.85714 |
| Mixtral 8x7B | tsar2025 | iso_examples | +0.769 | [-0.294, 1.831] | 0.20585 | 0.85714 | 0.57467 |

No primary contrast rejects under either BH scope. All raw corpus-mean bootstrap intervals include zero. The primary conclusion is unchanged.

## Secondary: ablated minus baseline

| Model | Dataset | Prompt | Delta SARI | 95% CI | Wilcoxon p | BH q (family 12) | BH q (all 24) |
|---|---|---|---:|---|---:|---:|---:|
| Llama 3.1 8B | cochrane | iso | +0.134 | [-0.469, 0.734] | 0.76184 | 0.8311 | 0.87067 |
| Llama 3.1 8B | cochrane | iso_examples | -0.254 | [-1.050, 0.545] | 0.44204 | 0.58939 | 0.85714 |
| Llama 3.1 8B | plaba | iso | +2.564 | [1.842, 3.293] | 2.505e-10 | 3.006e-09 | 6.012e-09 |
| Llama 3.1 8B | plaba | iso_examples | +2.764 | [1.876, 3.638] | 1.3124e-08 | 7.8745e-08 | 1.5749e-07 |
| Llama 3.1 8B | tsar2025 | iso | -0.331 | [-1.412, 0.751] | 0.32797 | 0.49196 | 0.71557 |
| Llama 3.1 8B | tsar2025 | iso_examples | -0.187 | [-1.310, 0.941] | 0.65862 | 0.79034 | 0.85714 |
| Mixtral 8x7B | cochrane | iso | -1.650 | [-2.459, -0.847] | 1.338e-05 | 3.2113e-05 | 6.4226e-05 |
| Mixtral 8x7B | cochrane | iso_examples | -1.424 | [-2.449, -0.431] | 0.001091 | 0.0021819 | 0.0043639 |
| Mixtral 8x7B | plaba | iso | -2.715 | [-3.767, -1.676] | 4.0056e-06 | 1.2017e-05 | 2.4034e-05 |
| Mixtral 8x7B | plaba | iso_examples | -1.078 | [-2.174, 0.004] | 0.2037 | 0.3492 | 0.57467 |
| Mixtral 8x7B | tsar2025 | iso | -3.448 | [-5.005, -1.911] | 1.7e-06 | 6.7999e-06 | 1.36e-05 |
| Mixtral 8x7B | tsar2025 | iso_examples | +0.614 | [-0.718, 2.005] | 0.83119 | 0.83119 | 0.88992 |

Six contrasts reject under both BH scopes: two positive Llama/PLABA contrasts; three negative Mixtral/ISO contrasts; and negative Mixtral/ISO+examples/Cochrane. All other secondary contrasts do not reject.

## Robustness and discrepancy

For Mixtral ISO+examples/Cochrane versus baseline, Wilcoxon p=0.001090970, BH family-12 q=0.002181941 and BH all-24 q=0.004363881. The prior permutation/Holm all-24 p is 0.10735. Both the test target and correction differ, so the discrepancy is not assigned solely to Holm or BH. The other 23 binary all-24 decisions agree. All methods and scopes are retained.

## Exact settings and limits

SciPy 1.17.1: zero_method=wilcox, correction=False, alternative=two-sided, method=auto. Per-item standard SARI is rounded to two decimals to match saved original item scores (verified for all 24 comparators); differences are scaled to integer centipoints to avoid artificial floating-point ties. Zero differences are omitted; all-zero comparisons receive p=1. Full W, pair counts, median differences and descriptive rank-biserial effects are in the CSV.

Raw mean deltas and existing 10,000-resample paired bootstrap intervals are unchanged. Signed-rank inference and mean-difference intervals address different aspects of the paired data under their respective assumptions. No equivalence or isolated ISO causality is established. PLABA within-document dependence remains unmodeled; capped and apparently incomplete outputs remain included.

The supplied manuscript declares Wilcoxon/BH, but its original statistical code/defaults/family definitions were unavailable. The same named methods and stored score precision are used here with explicit settings; bit-for-bit identity of the earlier statistical implementation is not claimed.
