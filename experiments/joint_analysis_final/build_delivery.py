"""Generate manuscript integration artifacts for the unified SARI analysis."""
from pathlib import Path
import hashlib
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'manuscript_proposals'
RESULTS = HERE / 'results'
LABELS = {'iso_minus_baseline': 'ISO -- Baseline', 'iso_examples_minus_baseline': 'ISO+examples -- Baseline',
          'iso_examples_minus_iso': 'ISO+examples -- ISO', 'one_minus_zero': 'One -- Zero',
          'few_random_minus_one': 'Few-random -- One', 'few_metric_minus_few_random': 'Few-metric -- Few-random',
          'few_retrieval_minus_few_random': 'Retrieval -- Few-random', 'few_retrieval_minus_few_metric': 'Retrieval -- Few-metric',
          'mixtral_minus_llama': 'Mixtral -- Llama'}
MODEL = {'llama': 'Llama', 'mixtral': 'Mixtral'}
DATASET = {'cochrane': 'Cochrane', 'plaba': 'PLABA', 'tsar2025': 'TSAR'}


def put(name, text):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + '\n', encoding='utf-8')


def qfmt(value):
    return '$<0.001$' if value < .001 else f'{value:.3f}'


def longtable(name, caption, label, spec, header, rows):
    heading = ' & '.join(header) + r' \\'
    put(name, '\\begingroup\n\\scriptsize\n\\setlength{\\tabcolsep}{3pt}\n\\begin{longtable}{' + spec + '}\n\\caption{' + caption + '}\\label{' + label + '}\\\\\n\\toprule\n' + heading + '\n\\midrule\n\\endfirsthead\n\\toprule\n' + heading + '\n\\midrule\n\\endhead\n' + '\n'.join(' & '.join(row) + r' \\' for row in rows) + '\n\\bottomrule\n\\end{longtable}\n\\endgroup')


def main():
    proof = json.loads((RESULTS / 'complete.json').read_text())
    for name, digest in {**proof['input_hashes'], **proof['output_hashes'], **proof['code_hashes']}.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    glob = pd.read_csv(RESULTS / 'global_sari.csv')
    local = pd.read_csv(RESULTS / 'local_sari.csv')
    omnibus = pd.read_csv(RESULTS / 'omnibus_sari.csv')
    rows = [[LABELS[r.contrast_id], f'{r.effect:+.3f}', f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]', qfmt(r.q_bh)] for r in glob.itertuples()]
    put('paper/01_global_sari_table.tex', r'''
\begin{table*}[t]
\centering
\caption{Global marginal SARI contrasts from the unified analysis, including retrieval. Differences are averaged equally over the relevant datasets, models, prompts and five strategies; random selections share their strategy's weight. Confidence intervals are pointwise 95\% source-group bootstrap intervals; $q$ values use BH adjustment over nine contrasts. No comparison is made to a post-selected best configuration.}
\label{tab:unified_global_sari}
\small
\begin{tabular}{lrrr}
\hline
Contrast & $\Delta$ SARI & 95\% bootstrap CI & $q_{BH}$ \\
\hline
''' + '\n'.join(' & '.join(row) + r' \\' for row in rows) + '\n\\hline\n\\end{tabular}\n\\end{table*}')
    localrows = []
    for r in local.itertuples():
        name, model, dataset = r.contrast_id.split('/')
        localrows.append([MODEL[model], DATASET[dataset], LABELS[name], f'{r.effect:+.3f}', f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]', qfmt(r.q_bh)])
    longtable('supplement/02_local_sari.tex', 'Model/dataset SARI contrasts from the unified fit. Prompt contrasts average five strategies; strategy contrasts average three prompts. BH adjustment covers all 48 contrasts in this family. Confidence intervals are pointwise, not multiplicity-adjusted.', 'tab:unified_local_sari', 'lllrrr', ['Model', 'Dataset', 'Contrast', '$\\Delta$', '95\\% bootstrap CI', '$q_{BH}$'], localrows)
    orows = []
    for r in omnibus.itertuples():
        term = r.term.replace('condition', 'strategy').replace('prompt', 'prompt type').replace('*', r' $\times$ ')
        orows.append([term, f'{r.F:.3f}', str(r.df_num), str(r.df_denom), qfmt(r.q_bh)])
    longtable('supplement/03_omnibus_sari.tex', 'All main effects and interactions of the four structural factors, tested on equal-selection-averaged cell means using the unified cluster-robust covariance. These are approximate Wald F tests, not classical ANOVA sums of squares. BH adjustment covers all 15 terms. Dataset differences refer to benchmark score levels, not causal domain effects.', 'tab:unified_omnibus_sari', 'lrrrr', ['Term', '$F$', 'df numerator', 'df denominator', '$q_{BH}$'], orows)
    struct = pd.read_csv(RESULTS / 'structural_means.csv')
    summary = struct.groupby(['model', 'dataset', 'condition']).SARI.mean().unstack()
    srows = []
    for (model, dataset), row in summary.iterrows():
        srows.append([MODEL[model], DATASET[dataset]] + [f'{row[c]:.3f}' for c in ['zero', 'one', 'few_random', 'few_metric', 'few_retrieval']])
    longtable('supplement/04_strategy_means.tex', 'Descriptive SARI means by model, dataset and strategy, averaged equally over three prompts and, where applicable, the three demonstration selections. These are not best-configuration scores or significance rankings.', 'tab:unified_strategy_means', 'llrrrrr', ['Model', 'Dataset', 'Zero', 'One', 'Few-random', 'Few-metric', 'Retrieval'], srows)
    methods = r'''
\subsection{Statistical Analysis}
\rev{To assess differences among prompting strategies, we conduct a joint statistical analysis and report estimated differences with confidence intervals. We use SARI as the primary metric and fit a joint fixed-effects model that estimates a separate mean for each observed configuration. The analysis includes 162 configurations defined by dataset, model, prompt type, prompting strategy, and demonstration selection where applicable. The five strategies are zero-shot, one-shot, random few-shot, fixed metric-based few-shot, and retrieval-based few-shot. One-shot and random few-shot each include selections 42, 44, and 46; the other strategies enter once. The remaining five metrics are summarized descriptively.}

\rev{Marginal contrasts assign equal weight to the datasets, models, prompt types, and strategies being averaged. Within each one-shot or random few-shot condition, the three selections share that condition's weight equally. Thus, evaluating three selections does not give these strategies greater weight than the fixed strategies. Selection is nested within the relevant conditions rather than treated as a fully crossed factor.}

\rev{Uncertainty is clustered by dataset and source identifier, preserving pairing across configurations. All 148 PLABA evaluation rows are retained, but rows sharing a source identifier are grouped together. There are 335 source groups: 125 Cochrane, 110 PLABA, and 100 TSAR. We use finite-sample-corrected cluster-robust standard errors for two-sided contrast tests and 10{,}000 dataset-stratified bootstrap resamples of source groups for pointwise 95\% confidence intervals. This uncertainty is conditional on the demonstration sets evaluated; it does not quantify variability over unseen selections.}

\rev{We evaluate nine global contrasts and 48 model--dataset contrasts, covering prompt differences, demonstration counts, selection strategies, and the two models. We also use cluster-robust Wald tests to examine the main effects and all interactions of dataset, model, prompt type, and strategy. The Benjamini--Hochberg procedure is applied separately to the families of nine global contrasts, 48 model--dataset contrasts, and 15 omnibus tests, using $q<0.05$. Confidence intervals are pointwise rather than multiplicity-adjusted. Failure to detect a difference does not establish equivalence. The full contrast definitions and computational protocol are provided in the Supplementary Material.}
'''
    put('paper/00_statistical_analysis_replacement.tex', methods)
    put('paper/02_unified_results.tex', r'''
\subsection{Joint Analysis of Prompting Strategies}
\rev{The unified SARI analysis does not detect an overall advantage of ISO or ISO+examples over Baseline ($\Delta=-0.135$, $q=0.284$; $\Delta=+0.044$, $q=0.767$). The ISO+examples--ISO difference is $+0.179$ points ($q=0.104$). In contrast, one-shot exceeds zero-shot by $0.820$ points, and random few-shot exceeds one-shot by $0.696$ points (both $q<0.001$). These are balanced marginal comparisons, not improvements established in every model--dataset setting.}

\rev{Within the three-demonstration conditions, retrieval exceeds the fixed metric-based selector by $0.542$ SARI points (95\% bootstrap CI $[0.246,0.839]$, $q<0.001$). The retrieval--random difference is $0.038$ points (CI $[-0.205,0.282]$, $q=0.767$), while the metric-based selector is $0.505$ points below random ($q<0.001$). Mixtral exceeds Llama by $0.597$ points in the balanced marginal comparison ($q=0.019$). Table~\ref{tab:unified_global_sari} reports all global estimates.}

\rev{The omnibus prompt-type main effect does not reach the adjusted threshold ($q=0.086$), whereas its interactions with model, dataset, and strategy do. The model-specific contrasts also differ in direction: ISO exceeds Baseline for Llama on Cochrane and PLABA, whereas ISO is below Baseline for Mixtral on all three datasets. The complete interaction tests and model--dataset contrasts are reported in the Supplementary Material.}
''')
    put('paper/03_RQ4_replacement.tex', r'''
The unified analysis compares random, fixed metric-based, and input-conditioned retrieval selection with three demonstrations. Averaged over the evaluated models, datasets, and prompts, retrieval and random both exceed the fixed metric-based selector in SARI, by $0.542$ and $0.505$ points, respectively. No retrieval--random difference is detected ($\Delta=0.038$, 95\% bootstrap CI $[-0.205,0.282]$, $q=0.767$); this is not evidence of equivalence.

The model--dataset contrasts qualify these averages. On PLABA, both random and retrieval exceed the metric-based selector for both models after adjustment over the 48 local contrasts. Retrieval is below random for Llama on TSAR ($\Delta=-0.926$, $q=0.019$). No other retrieval--random model--dataset contrast reaches the adjusted threshold. These comparisons average over prompt types; the separate prompt-specific results are supplementary historical analyses with different contrast families. The findings concern the evaluated heuristic, encoder, reference assignments and context constraints and do not establish that automatic selection methods generally outperform or underperform random selection.
''')
    put('paper/04_RQ1_RQ2_RQ3_RQ5_guidance.md', '''
# Discussion edits using the unified analysis

- RQ1: use ISO--Baseline -0.135 (q .284) and ISO+examples--Baseline +0.044 (q .767), not the earlier -0.183/+0.126. There is no detected overall advantage. Model × prompt and dataset × prompt interactions directly establish heterogeneity within the fixed study design; do not infer it solely by comparing subgroup significance labels. Local ISO effects are positive for Llama/Cochrane and Llama/PLABA and negative for Mixtral on all three datasets.
- RQ2: ISO+examples--ISO is now +0.179, q .104. Delete the old claim of a detectable global +0.309/q .0047 benefit. All five strategies enter the new prompt margins; retrieval changes the estimand. Local effects and original qualitative observations remain interpretable with their own scope, not as a global guarantee.
- RQ3: one--zero +0.820 and few-random--one +0.696 remain detectable globally. These are balanced comparisons, not uniform benefits for each setting and not pure causal demonstration-count effects detached from content. Selection is averaged within the random strategies; zero is not triplicated.
- RQ4: use 03_RQ4_replacement.tex and the new global/local q values. Old 18-per-prompt retrieval contrasts are preserved as supplementary historical analyses, not the new model/dataset margins.
- RQ5: direct omnibus interactions support configuration dependence. All six two-way interactions pass their 15-term BH family here. Do not attribute a quantitative portion of variance or a causal effect to any factor. Dataset score differences do not identify domain effects; models are two specific quantized systems. All higher-order terms are in the full table.

The figure requested under Concern 11 can use the unified contrast effects/intervals. Its layout/selection is a separate integration task; no figure has been generated by this statistical-analysis delivery. Abstract and conclusions below are coordinated replacements to review against live Overleaf and Alberto/Remi's independent additions.
''')
    put('paper/05_limitations_addition.tex', r'''
The unified analysis was extended during revision after the earlier selection and retrieval results had been inspected; it is not a preregistered confirmatory analysis. Its uncertainty is conditional on three constrained random demonstration sets, the evaluated retrieval procedure, and the observed models and datasets. Source-group resampling does not establish robustness over new demonstration selections. Historical controls, corrected example identifiers and runtime differences limit causal attribution of changes to selection alone. The analysis does not include the separate organization/summary ablation or repeat-penalty diagnostic, and non-significant contrasts are not equivalence tests.
''')
    put('paper/06_abstract_coordinated_draft.tex', r'''
This paper compares baseline and ISO-based prompts for text simplification using Llama~3.1~8B Instruct and Mixtral~8x7B Instruct. We evaluate Baseline, ISO, and ISO+examples prompts under zero-shot, one-shot, and three-demonstration few-shot conditions on Cochrane, PLABA, and TSAR~2025. Random demonstration selection is evaluated using three fixed selections; the few-shot comparison also includes a fixed metric-based selector and input-conditioned retrieval under a shared context constraint. We report six automatic metrics and output descriptors, complemented by illustrative qualitative analysis. A joint SARI analysis of all 162 observed configurations uses source-grouped uncertainty and balanced marginal contrasts. Neither ISO nor ISO+examples has a detectable overall advantage over Baseline, and prompt effects vary with model, dataset, and strategy. One-shot exceeds zero-shot and random few-shot exceeds one-shot in the marginal comparisons, without uniform improvement in every setting. Retrieval and random selection both exceed the evaluated fixed metric-based selector on average; no overall retrieval--random difference is detected. The findings are conditional on the tested models, demonstration sets, and evaluation protocol. They do not establish reader comprehension, complete meaning preservation, or compliance with ISO~24495-1.
''')
    put('paper/07_conclusions_coordinated_draft.tex', r'''
The unified SARI analysis does not identify an overall advantage of ISO or ISO+examples over Baseline under the tested conditions. The ISO+examples--ISO marginal difference also does not reach the adjusted threshold. Interactions show that prompt and strategy effects vary across the evaluated models and datasets, so their marginal averages should not be interpreted as uniform effects. One-shot exceeds zero-shot and random few-shot exceeds one-shot globally, while the three-selection summaries demonstrate sensitivity to demonstration choice in individual settings.

For three-demonstration selection, random and input-conditioned retrieval both exceed the fixed metric-based heuristic in the balanced global comparison. No overall retrieval--random difference is detected, without establishing equivalence. The model--dataset comparisons identify advantages over the metric heuristic on PLABA for both models and a retrieval disadvantage relative to random for Llama on TSAR. The results do not establish a universal ranking of demonstration-selection methods.

These conclusions concern automatic scores for the two evaluated models and observed demonstration sets. Readability, source similarity, output length and lexical reuse are complementary indicators, not evidence of reader comprehension, complete information preservation or ISO compliance. Historical controls and the revision-stage extension limit confirmatory and causal interpretations. The independent ablation and repeat-penalty findings should be integrated with their own experimental scope.
''')
    put('supplement/00_unified_protocol.tex', r'''
\section{Unified SARI Analysis Including Retrieval}
This revision-stage extension combines the main-study configurations after the earlier Concern 2 and Concern 5 outcomes had been inspected. The extension plan, contrast weights and hypotheses were saved before executing this unified analysis, but not before observing the earlier outcomes. It is not an external preregistration or an independent confirmatory replication. Previous analyses remain versioned separately.

The input comprises 162 observed cells and 20,142 response instances on 373 test rows and 335 source-identifier groups. The structural factors are dataset (Cochrane, PLABA, TSAR), model (Llama, Mixtral), prompt (Baseline, ISO, ISO+examples) and strategy (zero, one, few-random, few-metric, few-retrieval). One and few-random each have three fixed selections (42/44/46); the other strategies enter once. All empty and capped outputs and all 148 PLABA rows are retained. The 20,142 outputs are repeated observations on the same test material, not independent source texts. The separate ablation and repeat-penalty diagnostic are excluded.

The saturated cell-means model has 162 indicator columns and no additional intercept. Its means match the saved evaluation means exactly. Selection is nested in the relevant observed cells, not independently crossed with all strategies. Marginal contrasts first average the three selections within their structural condition and then give equal weight to factors being averaged. There are 90 selection-averaged structural cells. Prompt/model margins average five strategies, whereas the earlier Concern 2 analysis averaged four. Strategy contrasts average prompts. The reported sample SD across three selections remains a descriptive sensitivity measure rather than a random-effects variance estimate.

Source groups are defined by dataset and source identifier, with 125, 110 and 100 groups for Cochrane, PLABA and TSAR. The CR1 covariance correction is $G/(G-1)\,(N-1)/(N-P)$, where $G=335$, $N=20{,}142$ and $P=162$. Two-sided scalar contrasts use $t$ distributions with the number of source groups in their dataset support minus one degrees of freedom (334 globally; 124, 109 or 99 within dataset). A dataset-stratified document-group bootstrap samples groups with replacement, retaining their repeated rows and all conditions together (10,000 replicates, NumPy generator seed 20261104). Percentile 95\% intervals are pointwise and are not adjusted for multiplicity.

The nine global contrasts are ISO--Baseline, ISO+examples--Baseline, ISO+examples--ISO, one--zero, few-random--one, few-metric--few-random, few-retrieval--few-random, few-retrieval--few-metric and Mixtral--Llama. The first eight contrasts are repeated within the six model--dataset combinations, giving 48 local contrasts. BH adjustment is separate for the nine global and 48 local comparisons. No best-performing configuration is selected as the reference for these tests.

All 15 nonempty factorial terms of dataset, model, prompt and strategy are evaluated on the 90 structural means: four main effects, six two-way interactions, four three-way interactions and one four-way interaction. Hypotheses use tensor products of reference-level differences for included factors and uniform averages for omitted factors. Their null spaces do not depend on the chosen reference-level basis. Using the joint CR1 covariance, the Wald statistic is divided by the restriction rank and compared with an approximate $F$ distribution with that rank and 334 degrees of freedom. Restriction-covariance rank is verified; no singular constraints are silently removed. BH adjustment covers all 15 omnibus terms as a third family. These are not classical ANOVA sums of squares, and main effects represent averaged differences in the presence of interactions. Dataset effects describe benchmark score levels, not causal effects of domain.

All scalar estimates, SEs, raw $p$, adjusted $q$, degrees of freedom, intervals, restriction weights, sufficient statistics and bootstrap draws are retained in the repository. Statistical inference is limited to SARI; the other metrics are descriptive. Failure to reject is not equivalence. Prior Wilcoxon and earlier joint/retrieval results are retained as historical supplementary analyses; their annotations and adjusted values do not transfer to the unified analysis.
''')
    put('REVIEWER_RESPONSE_UPDATE.md', '''
# Unified response guidance for Concerns 2 and 5

**Prepared, not integrated.** The English completed-action text below applies only after updating the article/supplement. Do not overwrite the live response document or assert final page locations before compilation.

## Concern 2 statistical response — replace the old 144-cell/7+36 paragraph after integration

We revised the main statistical analysis to consider all main-study configurations jointly, including the retrieval comparison. The model uses a saturated fixed-effects cell-means parameterization for 162 observed configurations, with source-identifier-clustered uncertainty. It represents dataset, model, prompt type and the five observed prompting strategies, with the three random demonstration selections included only in the corresponding one-shot/random-few-shot cells. Equal-weight marginal contrasts prevent the random conditions from receiving triple weight and avoid constructing unobserved shot/selection combinations. The analysis retains 20,142 response instances and all repeated PLABA rows within 335 dataset/source-identifier groups.

We report nine global contrasts, 48 model/dataset-specific contrasts, and cluster-robust omnibus tests of all 15 main-effect/interaction terms of the four structural factors. BH adjustment is applied separately to these three declared families. Scalar contrasts include signed effects and pointwise 95% group-bootstrap intervals from 10,000 replicates. This supports direct interaction assessment rather than comparing subgroup significance labels or comparing every configuration to an observed best system. Neither non-rejection nor overlapping intervals are treated as evidence of equivalence. The individual three-selection scores and their sample SD remain available.

This unified extension was specified during revision after the earlier selection/retrieval results were known. We document that chronology, retain the earlier plans/results and do not describe the extension as preregistered or as independent confirmation. We retain original table/Wilcoxon evidence as clearly scoped historical supplementary results. The saturated model is not a mixed-effects model estimating an unrestricted distribution over three constrained demonstration sets.

## Concern 5 statistical response — align with the same unified analysis

The completed retrieval experiment is now included in the main unified analysis rather than described only by separate per-prompt comparisons. Globally, retrieval exceeds the fixed metric heuristic by 0.542 SARI points (95% bootstrap CI [0.246, 0.839], BH-adjusted q<.001). Its difference from the mean of the three random selections is 0.038 (CI [-0.205, 0.282], q=.767), without establishing equivalence. Local model/dataset contrasts average prompt types and use one 48-test BH family; both random and retrieval exceed the metric heuristic on PLABA for both models, and retrieval is below random for Llama on TSAR. The earlier 18+18 per-prompt comparisons remain versioned supplemental analyses, not the new global/local tests. Neither these comparisons nor the interaction terms establish a causal retrieval effect isolated from demonstration/reference/runtime differences.

## Claims requiring replacement

- Old global ISO+examples--ISO +0.309/q .0047 is replaced by +0.179/q .104 in the five-strategy unified analysis. Do not retain a significant overall advantage claim.
- Old global ISO--Baseline -0.183 and ISO+examples--Baseline +0.126 become -0.135 and +0.044, with q .284 and .767.
- The prior retrieval per-prompt four-positive/one-negative versus metric and one-positive/one-negative versus random counts remain true only for that earlier contrast scope/family. They are not counts of global or prompt-averaged model/dataset effects.
- Nine/48/15 BH families are revision-stage families, not the old prespecified 7/36 and 18/18 families. Never mix their q values in one table without clear labels.
- The former random/metric-only conclusions must incorporate retrieval and heterogeneity. Reader comprehension, human evaluation, CEFR control and comprehensive ISO compliance remain untested.
''')
    put('INSERTION_GUIDE.md', '''
# Main-study unified analysis — active integration guide

Use this guide for statistical Methods, Results and Discussion of the main study. It supersedes the earlier recommendation to present the 144-cell Concern 2 analysis and 18+18 Concern 5 contrasts as separate main analyses. Those earlier results remain preserved and their raw effect scopes remain valid; they are not overwritten. The live Overleaf has edits after main (2).tex; integrate by content anchors, not by stale line numbers.

1. Keep the accepted paragraph explaining random selections 42/44/46 in Demonstration Selection Strategies. Keep mean/sample SD tables and individual seed results. Add/retain the retrieval methods from Concern 5. Nothing in the unified statistical fit changes generation, examples or scores.
2. Replace the current statistical Methods block with `paper/00_statistical_analysis_replacement.tex`. It includes all five strategies. Use your accepted terminology `primary metric`, `prompt type` and `prompting strategy`. Add no duplicate old 144-cell/7+36 or main 18+18 retrieval statistical paragraph. Keep original Wilcoxon explanation beside original tables in the supplement, without transferring old annotations to new means.
3. Add `paper/01_global_sari_table.tex` and `paper/02_unified_results.tex` as the main inferential results. Preserve separate original/seed/retrieval descriptive tables with clear scope; the original six large tables can move to the supplement as requested by Concern 11. The requested effect figure is a subsequent formatting task, not generated here.
4. Add `supplement/00_unified_protocol.tex`, `02_local_sari.tex`, `03_omnibus_sari.tex` and `04_strategy_means.tex`. Load `longtable` and `booktabs`. Use final section numbers; never reference an external document label without external-reference tooling. Do not wrap a longtable in rev/hl.
5. Update RQ1/RQ2/RQ3/RQ5 using `paper/04_RQ1_RQ2_RQ3_RQ5_guidance.md`. Replace the selection discussion with `paper/03_RQ4_replacement.tex`, merging original explanatory context without retaining obsolete inference. Note in particular that ISO+examples--ISO no longer passes the global adjusted threshold.
6. Add/merge `paper/05_limitations_addition.tex`. The extension occurred after observing earlier outcomes; the main/supplement must not imply preregistration or independent confirmation. Keep limits on three constrained selections, historical comparators, automatic metrics and two models.
7. Coordinate abstract and conclusions with `paper/06_abstract_coordinated_draft.tex` and `07_conclusions_coordinated_draft.tex`. They are drafts for integration with the actual Overleaf and Alberto's ablation findings, not a claim that all concerns are closed. Preserve the finished Concern 6 edits and Remi's separate diagnostic scope.
8. Update the reviewer responses with `REVIEWER_RESPONSE_UPDATE.md` only after applying the changes. Final page/line references and final IEEE/supplement compilation remain pending.

## Reproduction and evidence

- `../ANALYSIS_PLAN.md` records scope, timing, estimands and all multiplicity families before this unified fit, but after earlier outcomes were known.
- `../design/frozen.json` pins the saved design/code. `../results/complete.json` pins all inputs and outputs.
- Reproduce/verify: `.\\.venv\\Scripts\\python.exe experiments/joint_analysis_final/run_analysis.py --execute`.
- Synthetic checks: `.\\.venv\\Scripts\\python.exe experiments/joint_analysis_final/test_analysis.py`.
- Tables/text generator: `.\\.venv\\Scripts\\python.exe experiments/joint_analysis_final/build_delivery.py`.
- CSVs: `../results/global_sari.csv`, `local_sari.csv`, `omnibus_sari.csv`, and `structural_means.csv`. All bootstrap draws and sufficient statistics are retained.

This local package is not automatically uploaded to GitHub and no live Overleaf or response Word file is modified. Old scripts/plans/outputs remain intact. Do not run older table generators expecting the new unified q values.
''')
    report = '# Unified main-study SARI analysis\n\nCompleted: 162 observed configurations, 90 selection-averaged structural cells, 20,142 repeated response instances, 335 source groups. All original scores retained; no inference or rescoring. This is a revision-stage extension after prior outcomes were known, not independent confirmation.\n\n## Global contrasts\n\n' + glob[['contrast_id', 'effect', 'bootstrap_ci_low', 'bootstrap_ci_high', 'q_bh']].to_csv(index=False)
    report += '\n## Interpretation\n\nNeither ISO nor ISO+examples has a detected global advantage over Baseline. ISO+examples--ISO is +0.179/q .104, replacing the earlier four-strategy +0.309/q .0047 conclusion. One--zero and random few--one remain positive globally. Retrieval (+0.542) and random (+0.505) both exceed the fixed metric heuristic globally; retrieval--random is +0.038/q .767, not equivalence. Mixtral--Llama is +0.597/q .019.\n\nOmnibus prompt main effect q .086 does not reject, but all six two-way interactions do, as do the reported higher-order interactions in this 15-term family. These are marginal linear hypotheses, not independent causal effects or explained-variance fractions. Dataset score differences reflect these benchmarks, not general domain difficulty.\n\nLocal prompt-averaged selection comparisons favor random and retrieval over metric on PLABA for both models; retrieval is below random for Llama/TSAR. Full local results, including non-rejections, are in local_sari.csv.\n\n## Change of estimand\n\nOriginal 144 cell means and 18 retrieval means are unchanged. Prompt/model global effects change because five strategies are now averaged rather than four. The same strategy contrast effects can have different p/q values because the fit size/CR1 correction and declared BH family changed. All bootstrap intervals are pointwise; the extension uses seed 20261104, 10,000 replicates. No winner is selected for testing.\n\n## Limits\n\nConditional on observed selections, models, datasets, reference policies and historical controls. Unseen demonstration sets, reader comprehension, CEFR control and ISO compliance are not inferred. No significance is claimed from comparing subgroup significance labels. Primary metric is SARI; other metrics/descriptors remain descriptive. Separate ablation and repeat-penalty studies are not pooled.\n'
    (HERE / 'REPORT.md').write_text(report, encoding='utf-8')
    proof = dict(status='prepared_not_integrated', files={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'})
    (OUT / 'manifest.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('Created unified integration package:', OUT)


if __name__ == '__main__':
    main()
