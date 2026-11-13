> Previous permutation/Holm-main version. Current version: [SCIENTIFIC_REPORT_WILCOXON_BH.md](SCIENTIFIC_REPORT_WILCOXON_BH.md).

# Focused organization/summary ablation — two-model scientific report

This is the current consolidated report. The earlier Llama-only report is
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

## 5. Metrics and inference

The six existing metric implementations are unchanged: standard evaluate SARI
(no legacy fallback), default sacrebleu corpus BLEU, English roberta-large
BERTScore-F1 without baseline rescaling, pinned earlier MeaningBERT against
the source, and mean textstat FKGL/FRE. TSAR uses A2/B1 references jointly.
MeaningBERT code and root checkpoint hashes are fixed by the shared provenance
record; the newer default model is not substituted.

Additional metrics: word count len(split()); mean per-item output/source word
ratio; mean proportion of exact case-sensitive output whitespace tokens that
occur in the source token set, punctuation retained. Copy rate is lexical
overlap on 0–1, not a verbatim phrase detector or meaning-preservation score.

Primary endpoint: unrounded SARI(ablated)−SARI(original). Each interval uses
10,000 paired percentile bootstrap samples of test rows, seed 42. Identical
sampled indexes apply to both conditions. The raw corpus implementation is
executed for both sampled datasets; only its deterministic normalization and
sentence kernel are cached. Full scores were checked against the public API.
Corpus BLEU is never estimated by averaging sentence BLEU.

Two-sided within-item randomization tests use 19,999 swaps and
(extreme+1)/(B+1). The original six-comparison Holm family for each model is
retained; an additional Holm correction across all 12 contrasts is reported.
Intervals are pointwise, not simultaneous. No model interaction or difference
between model effects has been tested. Complementary metrics remain descriptive.
The subsequent secondary baseline contrasts are documented in Section 11 below.

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

### Matched SARI comparisons

| Model | Dataset | Prompt | Original | Ablated | Delta | 95% CI | p | Holm (6) | Holm (12) |
|---|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | cochrane | iso | 38.40 | 38.44 | +0.047 | [-0.484, 0.573] | 0.86185 | 1.00000 | 1.00000 |
| Llama 3.1 8B | cochrane | iso_examples | 38.09 | 38.06 | -0.032 | [-0.444, 0.392] | 0.88490 | 1.00000 | 1.00000 |
| Llama 3.1 8B | plaba | iso | 36.30 | 36.37 | +0.075 | [-0.512, 0.654] | 0.80155 | 1.00000 | 1.00000 |
| Llama 3.1 8B | plaba | iso_examples | 36.68 | 36.57 | -0.102 | [-0.602, 0.412] | 0.69450 | 1.00000 | 1.00000 |
| Llama 3.1 8B | tsar2025 | iso | 46.68 | 46.93 | +0.254 | [-0.573, 1.092] | 0.54790 | 1.00000 | 1.00000 |
| Llama 3.1 8B | tsar2025 | iso_examples | 47.18 | 47.07 | -0.110 | [-0.877, 0.623] | 0.77625 | 1.00000 | 1.00000 |
| Mixtral 8x7B | cochrane | iso | 36.78 | 36.87 | +0.089 | [-0.621, 0.851] | 0.81810 | 1.00000 | 1.00000 |
| Mixtral 8x7B | cochrane | iso_examples | 37.12 | 37.09 | -0.022 | [-0.897, 0.828] | 0.95865 | 1.00000 | 1.00000 |
| Mixtral 8x7B | plaba | iso | 35.04 | 35.32 | +0.274 | [-0.736, 1.298] | 0.59130 | 1.00000 | 1.00000 |
| Mixtral 8x7B | plaba | iso_examples | 36.82 | 36.96 | +0.139 | [-0.885, 1.131] | 0.78615 | 1.00000 | 1.00000 |
| Mixtral 8x7B | tsar2025 | iso | 43.98 | 44.21 | +0.227 | [-0.974, 1.401] | 0.71615 | 1.00000 | 1.00000 |
| Mixtral 8x7B | tsar2025 | iso_examples | 47.50 | 48.27 | +0.769 | [-0.294, 1.831] | 0.15575 | 0.93450 | 1.00000 |

All 12 intervals include zero. No contrast rejects at 0.05 even without
multiple-comparison correction. Changes range from −0.110 to +0.769 points.
The largest point estimate is Mixtral ISO+examples on TSAR (+0.769,
CI [−0.294, 1.831], raw p=0.15575). This remains compatible with decreases
and increases and does not establish equivalence or absence of an effect.

Mixtral ISO mean length increases on all three datasets; ISO+examples length
increases on Cochrane but decreases on PLABA/TSAR. MeaningBERT decreases in
all six Mixtral ablations, whereas it increased in five Llama comparisons.
These are descriptive changes; no claim of significant meaning loss or
cross-model interaction is warranted. The full original/baseline metrics
are in [all_metrics.csv](all_metrics.csv).

The baseline ordering is model/dataset dependent: for example, Mixtral
ISO+examples on TSAR moves from 47.50 below baseline 47.66 to 48.27 above it.
The secondary baseline analysis does not statistically support that numerical
crossing as an improvement over baseline (see Section 11). No all-72-configuration claim follows from this study.

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

See [the updated English draft](REVIEWER2_CONCERN1_DRAFT.md). It is grounded in
these completed artifacts; manuscript insertion and real section/table numbers
remain pending. Other reviewer concerns are not claimed resolved. Original
prompts, inference outputs, saved scores and prior Llama analysis files are
preserved. No commit, push, release, tag move or external message was made.


## 11. Secondary ablated-versus-baseline extension

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

Proposed paper/supplement LaTeX fragments and exact placement instructions are in [latex_insertions](../latex_insertions/INSERTION_GUIDE.md). The supplied Downloads .tex files were read only.
