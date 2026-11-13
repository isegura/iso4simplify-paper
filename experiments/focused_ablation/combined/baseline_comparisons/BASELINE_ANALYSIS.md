# Secondary SARI comparisons with the baseline

Delta = ablated minus corresponding original baseline zero-shot. Values and intervals use unrounded standard SARI.

| Model | Dataset | Prompt | Delta | 95% CI | raw p | Holm 12 | Holm 24 |
|---|---|---|---:|---|---:|---:|---:|
| Llama 3.1 8B | cochrane | iso | +0.134 | [-0.469, 0.734] | 0.66110 | 1.00000 | 1.00000 |
| Llama 3.1 8B | cochrane | iso_examples | -0.254 | [-1.050, 0.545] | 0.53795 | 1.00000 | 1.00000 |
| Llama 3.1 8B | plaba | iso | +2.564 | [1.842, 3.293] | 0.00005 | 0.00060 | 0.00120 |
| Llama 3.1 8B | plaba | iso_examples | +2.764 | [1.876, 3.638] | 0.00005 | 0.00060 | 0.00120 |
| Llama 3.1 8B | tsar2025 | iso | -0.331 | [-1.412, 0.751] | 0.55760 | 1.00000 | 1.00000 |
| Llama 3.1 8B | tsar2025 | iso_examples | -0.187 | [-1.310, 0.941] | 0.74285 | 1.00000 | 1.00000 |
| Mixtral 8x7B | cochrane | iso | -1.650 | [-2.459, -0.847] | 0.00010 | 0.00080 | 0.00200 |
| Mixtral 8x7B | cochrane | iso_examples | -1.424 | [-2.449, -0.431] | 0.00565 | 0.03955 | 0.10735 |
| Mixtral 8x7B | plaba | iso | -2.715 | [-3.767, -1.676] | 0.00005 | 0.00060 | 0.00120 |
| Mixtral 8x7B | plaba | iso_examples | -1.078 | [-2.174, 0.004] | 0.05360 | 0.32160 | 0.96480 |
| Mixtral 8x7B | tsar2025 | iso | -3.448 | [-5.005, -1.911] | 0.00005 | 0.00060 | 0.00120 |
| Mixtral 8x7B | tsar2025 | iso_examples | +0.614 | [-0.718, 2.005] | 0.39350 | 1.00000 | 1.00000 |

## Interpretation

Five contrasts survive correction across all 24 primary and secondary comparisons: both Llama variants are above baseline on PLABA, and Mixtral ISO ablated is below baseline on all three datasets. Mixtral ISO+examples on Cochrane is below baseline after Holm across the 12 secondary tests (0.03955), but not after Holm across all 24 (0.10735). Other secondary contrasts do not reject after correction. The pointwise intervals are not multiplicity-adjusted; an interval excluding zero can coexist with a non-significant globally adjusted test.

The original 12 ablated-versus-original comparisons remain unchanged, all non-significant. These are distinct questions: similarity to the original ISO prompt is not evidence of similarity to baseline. No equivalence, mediation or complete causal ISO effect is established.

## Method

10,000 paired item percentile bootstrap resamples; 19,999 two-sided within-item swaps; add-one Monte Carlo p-values; seed 20261022 with independent per-comparison streams. The installed raw corpus SARI implementation is evaluated on both resampled datasets, with exact deterministic inner-call caching. Reference handling and all capped/apparently incomplete outputs are preserved. The resampling unit is the row, ignoring possible shared-document dependence in PLABA. Findings are conditional on fixed model runs and test sets. Historical generation runtime identity is not guaranteed.

Primary-family Holm-12 and secondary-family Holm-12 are separately reported; global Holm-24 is a conservative additional analysis. No result is selected solely by whichever correction is more favorable. Full provenance and input hashes are in methodology.json.
