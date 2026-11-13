# Focused organization/summary ablation — two models, Wilcoxon/BH main analysis

This is the current consolidated report with Wilcoxon/BH as the main analysis. Earlier permutation/Holm and Llama-only versions are
retained as historical evidence. The manuscript and submission tag v1.0.3
(user-confirmed) have not been edited, committed or published.

## 1. Objective

Test the contribution of the explicit information-hierarchy, initial-summary
and logical-grouping block in the existing ISO and ISO+examples prompts,
addressing Reviewer #2 Concern #1 through the requested focused ablation.
This is not a length-matched non-ISO control and does not identify the entire
causal effect of ISO 24495-1.

## 2. Exact prompt change

The two ablated prompt files are exact byte copies outside removal of the
PRINCIPLES OF ORGANIZATION AND HIERARCHY heading and its three instructions.
See [ISO diff](../iso.diff) and [ISO+examples diff](../iso_examples.diff).
ROLE, MISSION, ISO framing, all linguistic instructions, omission permissions,
VISUAL FORMAT, RESPONSE FORMAT and all illustrative examples remain.
Baseline prompts are unchanged. In particular, lists remain requested after
ablation; the intervention does not remove every source of organization cues.

## 3. Experimental design

Two models × two ablated prompts × three datasets = 12 new zero-shot
configurations, 1,492 generated outputs. Cochrane uses 125 rows, PLABA 148,
TSAR2025 100 per configuration. Original sources/references/ordering were
checked by row, ID, source and reference. No preprocessing or postprocessing
change was introduced. All 12 executions completed without empty predictions.
Execution completeness does not establish linguistic/content completeness.

Nine original zero-shot comparator cells per model (baseline, ISO, ISO+examples
on each dataset) were recomputed, giving 30 aggregate evaluation cells total.
All 108 saved original aggregate metric values are reproduced exactly at
their reported precision. See each model's original_score_check.csv.

## 4. Model and evaluation setup

Both use Ollama with output cap 512, num_ctx 8192, temperature 0, seed 42,
top_k 1, top_p 1, repeat_penalty 1.1, repeat_last_n 64, num_gpu 999, GPU
required and timeout 900 seconds, matching the original logs. GPU-use checks
do not guarantee that all model layers fit entirely in VRAM.

- Llama: llama3.1:8b, Q4_K_M, digest
  46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e.
- Mixtral: mixtral:latest, Q4_0, digest
  a3b6bef0f836ff29ddb576a80eeb1b7def43ec9b809466f62e96adb871fe8498.
- New inference runtime: Ollama 0.40.6. Historical binary/runtime identity is
  not certified by the old logs despite matching decoding parameters.
- Evaluation: separate .venv-eval, PyTorch 2.10.0+cu128; other pinned package
  versions preserved. BERTScore uses CUDA; original MeaningBERT runs on CPU.

## 5. Metrics and statistical inference — current protocol

The six original metric implementations and three descriptive definitions are unchanged, including pinned original MeaningBERT, TSAR multireference handling and the corpus BLEU calculation. The original 108 aggregate score reproduction checks remain valid.

Main significance tests now use paired two-sided Wilcoxon with BH, matching the named protocol in the manuscript. Each contrast uses per-item standard SARI at two decimals, verified against original stored item values, with integer centipoint differences to preserve numerical ties. SciPy 1.17.1 uses zero_method=wilcox, no continuity correction and method=auto. Exact previous statistical defaults were unavailable; no bit-for-bit historical statistical identity is claimed.

Twelve primary ablated-original and twelve secondary ablated-baseline tests form separate fixed BH families. All-24 BH is also reported. Raw corpus-mean effects and pointwise paired bootstrap intervals are unchanged. These intervals and signed-rank tests do not have identical inferential targets. Earlier permutation/Holm results remain a separately labeled robustness check.

## 6. Quantitative results

### Twelve ablations: nine metrics

| Model | Dataset | Prompt | SARI | BLEU | BERTScore-F1 | MeaningBERT | FKGL | FRE | Words | Compression | Copy rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | cochrane | iso_ablated | 38.44 | 8.97 | 0.8639 | 72.87 | 10.31 | 47.67 | 187.07 | 0.5877 | 0.6692 |
| Llama 3.1 8B | cochrane | iso_examples_ablated | 38.06 | 12.35 | 0.8656 | 80.16 | 10.60 | 43.84 | 188.92 | 0.5743 | 0.8080 |
| Llama 3.1 8B | plaba | iso_ablated | 36.37 | 9.58 | 0.8759 | 68.90 | 9.95 | 51.61 | 148.90 | 0.7348 | 0.5400 |
| Llama 3.1 8B | plaba | iso_examples_ablated | 36.57 | 11.07 | 0.8810 | 74.77 | 10.46 | 47.93 | 138.89 | 0.6729 | 0.6302 |
| Llama 3.1 8B | tsar2025 | iso_ablated | 46.93 | 30.54 | 0.9208 | 79.82 | 7.59 | 65.53 | 73.76 | 0.8722 | 0.5860 |
| Llama 3.1 8B | tsar2025 | iso_examples_ablated | 47.07 | 32.63 | 0.9337 | 85.20 | 7.49 | 66.52 | 65.62 | 0.7553 | 0.6857 |
| Mixtral 8x7B | cochrane | iso_ablated | 36.87 | 8.75 | 0.8558 | 73.88 | 10.09 | 45.94 | 181.09 | 0.5804 | 0.7023 |
| Mixtral 8x7B | cochrane | iso_examples_ablated | 37.09 | 10.98 | 0.8573 | 75.56 | 9.87 | 48.39 | 198.29 | 0.6351 | 0.7630 |
| Mixtral 8x7B | plaba | iso_ablated | 35.32 | 10.07 | 0.8774 | 69.52 | 10.42 | 47.53 | 135.48 | 0.6596 | 0.5883 |
| Mixtral 8x7B | plaba | iso_examples_ablated | 36.96 | 12.75 | 0.8833 | 74.54 | 10.91 | 46.04 | 144.82 | 0.7125 | 0.6663 |
| Mixtral 8x7B | tsar2025 | iso_ablated | 44.21 | 24.27 | 0.9276 | 80.36 | 8.72 | 58.08 | 66.81 | 0.7762 | 0.5406 |
| Mixtral 8x7B | tsar2025 | iso_examples_ablated | 48.27 | 33.39 | 0.9422 | 83.71 | 8.25 | 62.20 | 68.46 | 0.7892 | 0.6532 |



### Main Wilcoxon/BH comparisons

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

### Generation-cap terminations

| Model | Dataset | Prompt | n | Original length | Ablated length |
|---|---|---|---|---|---|
| Llama 3.1 8B | cochrane | iso | 125 | 0 | 1 |
| Llama 3.1 8B | cochrane | iso_examples | 125 | 5 | 7 |
| Llama 3.1 8B | plaba | iso | 148 | 0 | 0 |
| Llama 3.1 8B | plaba | iso_examples | 148 | 0 | 0 |
| Llama 3.1 8B | tsar2025 | iso | 100 | 0 | 0 |
| Llama 3.1 8B | tsar2025 | iso_examples | 100 | 0 | 0 |
| Mixtral 8x7B | cochrane | iso | 125 | 7 | 17 |
| Mixtral 8x7B | cochrane | iso_examples | 125 | 29 | 30 |
| Mixtral 8x7B | plaba | iso | 148 | 0 | 1 |
| Mixtral 8x7B | plaba | iso_examples | 148 | 7 | 7 |
| Mixtral 8x7B | tsar2025 | iso | 100 | 0 | 0 |
| Mixtral 8x7B | tsar2025 | iso_examples | 100 | 0 | 0 |

All outputs are retained in primary analyses. In Cochrane, differential cap
termination can affect matched comparisons. No non-truncated sensitivity
analysis is claimed. A run finishing successfully and an output receiving
stop are not evidence that the text is semantically complete.

## 7. Qualitative review

Both models use the same prespecified five source positions per dataset:
Cochrane 0/31/62/93/124, PLABA 0/36/73/110/147, TSAR 0/24/49/74/99.
This yields 60 paired output comparisons over the same 15 sources, not 30
independent sources. Selection was not based on metrics or observed errors.
Full texts and case notes: [Llama review](../qualitative/QUALITATIVE_REVIEW.md)
and [Mixtral review](../mixtral/qualitative/QUALITATIVE_REVIEW.md).

Exploratory inspection found preserved chronological/source ordering and
heterogeneous segmentation. Numbered lists can appear or persist after the
block is removed: Mixtral TSAR45 ISO changes from a paragraph to five points;
Cochrane CD011655 ISO similarly becomes numbered. Original prompts also do
not consistently produce an initial standalone summary. These observations
do not isolate a mechanism; formatting instructions remain in both conditions.

Mixtral additionally shows sample outputs that end in partial numbers or
introductions with stop rather than length. Cochrane CD009601 ISO+examples
ablated ends at “Some studies compared:”; CD008053 ends at “a total of 1”.
PLABA27630909 has fragmentary outputs in both prompt families and conditions.
These are observed apparent content failures, not diagnosed token-cap events.
PLABA34477130 ISO+examples original does end with length; its ablation reaches
a conclusion with stop. Such pairs confound judgments of structure with
coverage/termination. No cause such as repeat penalty, stop sequences,
quantization or input clipping is asserted without a separate diagnostic.

This is AI-assisted exploratory inspection, not a human evaluation, an ISO
adherence rate or a population error-frequency estimate. There were no blinded
independent raters, adjudication, comprehension tasks or agreement statistics.

## 8. Limitations

- Zero-shot, two existing models and one deterministic generation per cell;
  no inference across demonstration seeds or additional models.
- Historical model/runtime identity uncertain; matching parameters alone do
  not eliminate runtime confounding across original/new generations.
- Prompt length, instruction count, omission permissions and retained format
  instructions are not jointly controlled; no length-matched non-ISO control.
- Reference-based metrics do not measure hierarchy, summary-first quality,
  compliance with ISO or usefulness to readers. No equivalence margin/test.
- Row-based PLABA resampling ignores possible shared-document dependence;
  repeated IDs were explicitly left uninvestigated by the user.
- Cochrane generation-cap rates differ, and stop can accompany an apparently
  incomplete text. No removal or repair of such outputs in the primary study.
- Small nonrandom qualitative sample with no independent human assessment.

## 9. Implications for RQ1/RQ2

The new defensible statement is restricted: in both existing models' tested
zero-shot settings, removing this explicit block yielded no statistically
detectable SARI change in any of 12 comparisons. This extends the Llama-only
finding to the second existing model, without establishing equivalence,
invariance, ISO adherence or the full causal effect of ISO. The effects are
not shown equal across models; no interaction test was performed. The study
does not answer questions about demonstration selection or one/few-shot runs.
The subsequently supplied manuscript defines RQ1 as ISO-based versus baseline
prompt performance and RQ2 as the contribution of embedded examples. These
ablations and secondary baseline contrasts inform RQ1, but do not directly test
the incremental effect of adding examples to ablated prompts.

## 10. Reviewer response and artifact status

See [the current English draft](REVIEWER2_CONCERN1_WILCOXON_BH.md). It is grounded in
these completed artifacts; manuscript insertion and real section/table numbers
remain pending. Other reviewer concerns are not claimed resolved. Original
prompts, inference outputs, saved scores and prior Llama analysis files are
preserved. No commit, push, release, tag move or external message was made.
