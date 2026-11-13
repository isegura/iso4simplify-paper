# Unified SARI analysis including retrieval — 4 November 2026

## Status and provenance

This extension is specified before executing its unified contrasts, but AFTER the original Concern 2 and Concern 5 scores, comparisons and conclusions were inspected. It is an outcome-informed revision-stage extension, not a preregistration or an independent confirmatory replication. Do not describe its new families as prespecified before observing the study outcomes. Earlier plans/results remain unchanged and auditable.

Purpose: provide one coherent statistical analysis of all evaluated main-study configurations, including per-input retrieval, rather than selecting a winner and testing all configurations against it. The additional organization/summary ablation (Concern 1) and repeat-penalty diagnostic (Concern 4) are separate experiments and are not pooled with the main study.

## Inputs and model

SARI is the only inferential metric. Use existing rounded instance scores without regeneration, rescoring, exclusion or selection of a favorable seed. The other five metrics and the between-selection SD remain descriptive. Include 162 observed configuration cells and 20,142 response instances: 144 cells/17,904 instances from the verified Concern 2 analysis plus 18 cells/2,238 retrieval instances. These are repeated outputs on 373 evaluation rows, not 20,142 independent source texts. The 335 dataset/source-ID groups comprise 125 Cochrane, 110 PLABA and 100 TSAR groups. Preserve all 148 PLABA rows and all empty/capped outputs.

Fit the existing saturated fixed-effects cell-means regression (one indicator per observed dataset/model/prompt/strategy/selection cell, no extra intercept). The complete structural design has dataset (3 levels), model (2), prompt (3), and strategy (5: zero, one, few_random, few_metric, few_retrieval). One and few_random each have selections 42/44/46; the other strategies enter once. Selection is nested in the corresponding dataset/strategy cells and is NOT an independently crossed five-way factor, nor a random effect distribution estimable from three constrained sets. Retrieval varies examples per target as already specified; it is not assigned three fictitious random seeds. Likewise shots and selection method are not crossed into nonexistent zero/one-metric or one-retrieval cells.

Source-cluster sufficient statistics preserve pairing across every strategy, prompt, model and observed selection. CR1 covariance uses G/(G-1)*(N-1)/(N-P), with G=335, N=20142 and P=162. Differences use two-sided t tests with support-group-count minus one degrees of freedom. Marginal means give each dataset, model, prompt and strategy being averaged equal weight. Each random strategy's three selections split its structural-cell weight equally. Dataset means retain their original within-dataset row weighting. In particular, random strategies do not receive three times the weight of fixed strategies. Prompt/model margins now average FIVE strategies, unlike the four-strategy historical Concern 2 analysis.

## Family 1: nine global SARI contrasts

Compute equal-weight marginal differences from the SAME joint fit:

1. ISO minus Baseline (average all five strategies, models and datasets).
2. ISO+examples minus Baseline (same margins).
3. ISO+examples minus ISO (same margins).
4. One minus zero (average prompts/models/datasets; selections averaged within one).
5. Few-random minus one (same margins; average the matched selections).
6. Few-metric minus few-random (same margins).
7. Few-retrieval minus few-random (same margins).
8. Few-retrieval minus few-metric (same margins).
9. Mixtral minus Llama (average five strategies/prompts/datasets).

BH-adjust all nine as one family. These contrasts directly address prompt design, examples, the tested demonstration counts, selection methods and model differences. They are not comparisons to a post-selected best system. Do not infer a causal effect of demonstration number or selection independently of the observed content/reference/runtime differences.

## Family 2: 48 model/dataset contrasts

Repeat contrasts 1–8 within each of the six model/dataset settings (3 prompt contrasts plus 5 strategy contrasts). Adjust all 48 together as a second BH family, not six independent families. Prompt contrasts still average five strategies; strategy contrasts average three prompts. These quantify conditional effects with intervals rather than comparing significance labels between subgroups.

## Family 3: all 15 factorial omnibus terms

On the 90 equal-selection-averaged structural cell means, test every nonempty subset of the four structural factors: four main effects, six two-way interactions, four three-way interactions and one four-way interaction. This full, fixed list avoids choosing an interaction after inspecting which is significant. Construct hypotheses from tensor products of reference-level difference contrasts for included factors and uniform margins for omitted factors. For example, prompt × model tests whether prompt differences vary by model, averaged over datasets and five strategies. Its null is not inferred from separate subgroup significance tests. A main effect is an averaged effect in the presence of interactions, not a constant effect or a variance contribution.

Use the joint CR1 covariance and Wald F=W/rank(R) with rank(R) numerator degrees of freedom and G-1=334 denominator degrees of freedom. These are approximate cluster-robust Wald tests, NOT exact classical ANOVA F tests or sums-of-squares decompositions. Require full-rank restriction covariance; fail for inspection if singular, do not silently drop constraints or change the test. BH-adjust the 15 omnibus p values together. No extra post-hoc three-method win-count tests.

Dataset main-effect tests compare these three benchmark score levels and do not identify a causal domain effect or a population of datasets. Model main-effect tests are conditional on the two systems/checkpoints/quantizations. Higher-order interactions remain in the complete supplementary output even if unwieldy for the article. They do not warrant causal interpretations.

## Intervals and reporting

For all 57 scalar contrasts, jointly resample whole source-ID groups within each dataset, 10,000 draws using NumPy default_rng seed 20261104. Keep all repeated PLABA rows, configurations and selections for a sampled group. Recompute cell means and contrasts in each draw; use 2.5/97.5 percentiles for pointwise 95% intervals. Do not treat these as multiplicity-adjusted intervals; adjusted q values determine the stated BH decisions. No bootstrap hypothesis-test substitution for the declared CR1 tests. This quantifies source-group uncertainty conditional on the observed selections, not variability over unseen demonstration sets, models or corpora.

Report signed differences, SE, raw p, adjusted q, t degrees of freedom, percentile intervals and Wald omnibus terms. Preserve non-rejections as lack of detected differences, never equivalence. Report every family, not only discoveries. Retain the individual 42/44/46 results and sample SD; the unified regression does not make a three-seed robustness claim. The original Wilcoxon/72-table annotations are historical supplementary evidence and are not reassigned to new means.

## Validation and dependencies

Validate every original frozen plan, raw-input hash, item/certificate hash, test alignment and original audit before assembly. Compare original 144 and retrieval 18 fitted cell means to their separately verified saved evaluations. Test balanced margins and nesting; compare CR1 with expanded-data OLS/sandwich; compare tensor omnibus tests with an independent implementation on synthetic data, including repeated source rows and a known interaction. Preserve plans, code hashes, all sufficient statistics, contrast/restriction weights and joint bootstrap draws. Re-running must verify rather than overwrite completed results. No downloads or LLM inference.

Technical reference for the Wald F implementation (not a claim that a citation prescribes this study design): https://www.statsmodels.org/stable/_modules/statsmodels/base/model.html . The implementation uses q.T @ inv(R V R.T) @ q / rank(R), consistent with the documented linear-hypothesis machinery. Source-group covariance/bootstrap reuse the already tested Concern 2 core.

## Editorial integration

Use this expanded analysis as the main-study SARI inference for Concerns 2/5 and RQ1–RQ5. Preserve earlier analyses as versioned historical results, explaining changed estimands and BH families; do not copy their q values into final tables. Prepare replacement statistical methods, global/local/omnibus tables, results/discussion, coordinated abstract/conclusion proposals and updated reviewer-response guidance. Do not overwrite the user's live Overleaf text, Concern 1/4 contributions or historical frozen artifacts. Final language should disclose the revision-stage extension and prior outcome inspection; no 'prespecified before generation' claim for these new unified comparisons.
