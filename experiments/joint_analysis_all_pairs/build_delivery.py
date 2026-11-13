"""Generate the all-pairs integration package without modifying earlier outputs."""
from pathlib import Path
import importlib.util
import json
import hashlib
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'experiments/joint_analysis_final'
OUT = HERE / 'manuscript_proposals'


def put(name, text):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip()+'\n', encoding='utf-8')


def main():
    spec = importlib.util.spec_from_file_location('previous_table_helpers', OLD / 'build_delivery.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    helper.OUT = OUT
    labels = dict(helper.LABELS)
    labels.update(few_random_minus_zero='Few-random -- Zero', few_metric_minus_zero='Few-metric -- Zero',
                  few_retrieval_minus_zero='Retrieval -- Zero', few_metric_minus_one='Few-metric -- One',
                  few_retrieval_minus_one='Retrieval -- One')
    glob = pd.read_csv(HERE / 'results/global_sari.csv')
    local = pd.read_csv(HERE / 'results/local_sari.csv')
    rows = [[labels[r.contrast_id], f'{r.effect:+.3f}', f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]', helper.qfmt(r.q_bh)] for r in glob.itertuples()]
    put('paper/01_global_sari_table.tex', r'''
\begin{table*}[t]
\centering
\caption{Global marginal SARI contrasts from the unified analysis. All ten pairs of the five strategies are evaluated, together with three prompt comparisons and the model comparison. Differences use equal structural weights and equal weights within random selections. Intervals are pointwise 95\% source-group bootstrap intervals; BH adjustment covers all 14 global comparisons.}
\label{tab:unified_global_sari}
\small
\begin{tabular}{lrrr}
\hline
Contrast & $\Delta$ SARI & 95\% bootstrap CI & $q_{BH}$ \\
\hline
''' + '\n'.join(' & '.join(row)+r' \\' for row in rows) + '\n\\hline\n\\end{tabular}\n\\end{table*}')
    lrows = []
    for r in local.itertuples():
        key, model, dataset = r.contrast_id.split('/')
        lrows.append([helper.MODEL[model], helper.DATASET[dataset], labels[key], f'{r.effect:+.3f}', f'[{r.bootstrap_ci_low:+.3f}, {r.bootstrap_ci_high:+.3f}]', helper.qfmt(r.q_bh)])
    helper.longtable('supplement/02_local_sari.tex', 'All 13 prompt/strategy contrasts within each of six model--dataset settings. Prompt contrasts average five strategies; strategy contrasts average three prompts. BH correction is over the full 78-test family. Intervals are pointwise.', 'tab:unified_local_sari', 'lllrrr', ['Model', 'Dataset', 'Contrast', '$\\Delta$', '95\\% bootstrap CI', '$q_{BH}$'], lrows)
    for name in ['supplement/03_omnibus_sari.tex', 'supplement/04_strategy_means.tex']:
        put(name, (OLD / 'manuscript_proposals' / name).read_text())
    previous = OLD / 'manuscript_proposals'
    methods = (previous / 'paper/00_statistical_analysis_replacement.tex').read_text()
    prefix = methods.split(r'\rev{We evaluate nine global contrasts')[0]
    put('paper/00_statistical_analysis_replacement.tex', prefix + r'''
\rev{We evaluate all ten pairwise comparisons among the five prompting strategies, the three pairwise comparisons among prompt types, and Mixtral versus Llama, giving 14 global contrasts. The ten strategy and three prompt contrasts are also evaluated within each model--dataset combination, giving 78 additional contrasts. We use cluster-robust Wald tests for the 15 main-effect and interaction terms of dataset, model, prompt type, and strategy. Benjamini--Hochberg correction is applied separately to the 14 global contrasts, 78 model--dataset contrasts, and 15 omnibus tests, with $q<0.05$. Confidence intervals are pointwise and are not adjusted for multiple comparisons. Failure to detect a difference does not establish equivalence. Full definitions and implementation details are provided in the Supplementary Material.}
''')
    # Supplement preserves every prior implementation detail, replacing only the changed family definition.
    protocol = (previous / 'supplement/00_unified_protocol.tex').read_text()
    oldparagraph = next(p for p in protocol.split('\n\n') if p.startswith('The nine global contrasts'))
    protocol = protocol.replace(oldparagraph, r'''The 14 global contrasts comprise all ten pairs among zero, one, few-random, few-metric and few-retrieval; all three prompt pairs; and Mixtral--Llama. Each strategy pair is oriented as the later strategy in the listed order minus the earlier strategy. The ten strategy and three prompt contrasts are repeated within each of the six model--dataset combinations, giving 78 local contrasts. BH adjustment covers all 14 global tests and, separately, all 78 local tests. No best configuration is selected as reference. This all-pairs extension was recorded after inspecting earlier outcomes; it is not preregistered. The model, covariance, original scores and 15-term omnibus hypotheses are unchanged from the earlier unified fit. Shared scalar effects, SEs, raw p values and bootstrap intervals match the preceding version; scalar adjusted values belong to the new 14/78 families.''')
    put('supplement/00_unified_protocol.tex', protocol)
    put('paper/02_unified_results.tex', r'''
\subsection{Joint Analysis of Prompting Strategies}
\rev{The unified analysis does not detect a global SARI advantage of ISO or ISO+examples over Baseline ($\Delta=-0.135$, $q=0.258$; $\Delta=+0.044$, $q=0.767$). The ISO+examples--ISO difference is $+0.179$ ($q=0.097$). One-shot exceeds zero-shot by $0.820$ points. All three few-shot strategies also exceed zero-shot: random by $1.517$, metric-based by $1.012$, and retrieval by $1.555$ points (all four adjusted $q<0.001$). Relative to one-shot, random few-shot and retrieval have positive differences of $0.696$ and $0.734$ points (both $q<0.001$), whereas the metric-based few-shot difference of $0.192$ is not detected ($q=0.101$).}

\rev{Among the three few-shot strategies, retrieval exceeds the fixed metric selector by $0.542$ points ($q<0.001$), and random exceeds metric by $0.505$ points ($q<0.001$). The retrieval--random difference is $0.038$ (95\% bootstrap CI $[-0.205,0.282]$, $q=0.767$), without establishing equivalence. Mixtral exceeds Llama by $0.597$ points ($q=0.016$). These are balanced marginal differences, not uniform effects in all model--dataset settings. Table~\ref{tab:unified_global_sari} gives all 14 global estimates.}

\rev{The 15 omnibus tests retain the same results as the preceding unified fit: the prompt main effect does not pass adjustment ($q=0.086$), but its interactions with model, dataset and strategy do. All 78 local contrasts, including non-rejections, are reported in the Supplementary Material. Their q values use the expanded 78-test family and should not be interchanged with earlier adjusted values.}
''')
    abstract = (previous / 'paper/06_abstract_coordinated_draft.tex').read_text()
    abstract = abstract.replace('One-shot exceeds zero-shot and random few-shot exceeds one-shot in the marginal comparisons, without uniform improvement in every setting.', 'One-shot and all three few-shot strategies exceed zero-shot in the marginal comparisons; random few-shot and retrieval also exceed one-shot, without uniform improvement in every setting.')
    put('paper/06_abstract_coordinated_draft.tex', abstract)
    conclusion = (previous / 'paper/07_conclusions_coordinated_draft.tex').read_text()
    conclusion = conclusion.replace('One-shot exceeds zero-shot and random few-shot exceeds one-shot globally,', 'One-shot and all three few-shot strategies exceed zero-shot globally; random few-shot and retrieval also exceed one-shot,')
    # Prior local q values are not retained here; full local output is authoritative.
    put('paper/07_conclusions_coordinated_draft.tex', conclusion)
    put('paper/05_limitations_addition.tex', (previous / 'paper/05_limitations_addition.tex').read_text())
    local_comp = local[local.contrast_id.str.contains('few_retrieval_minus_few_random|few_retrieval_minus_few_metric|few_metric_minus_few_random')]
    put('DISCUSSION_AND_RESPONSE_GUIDANCE.md', '''
# Active conclusions and reviewer response — all strategy pairs

The new statistical scope is 14 global contrasts, 78 local model/dataset contrasts and 15 unchanged omnibus terms. These are three separately BH-adjusted families. All ten pairs of the five strategies are included without selecting a winning configuration. The expansion is revision-stage, after earlier outcomes were known; it is not independent confirmation or preregistration.

For RQ3, all few-shot variants have positive adjusted global differences from zero-shot. Random and retrieval also exceed one-shot globally; few-metric versus one-shot is not detected. For RQ1/RQ2, neither ISO prompt exceeds Baseline globally and ISO+examples versus ISO remains non-significant (q .097). For RQ4, random and retrieval exceed the fixed metric heuristic; retrieval versus random is not detected and does not establish equivalence. The comparisons are between evaluated strategy bundles, not pure causal effects of example count or retrieval alone. All original interaction results remain unchanged.

Updated local selection effects/q values (full precision in CSV):
''' + local_comp[['contrast_id', 'effect', 'q_bh']].to_csv(index=False) + '''

Use results/global_sari.csv and local_sari.csv for numbers; do not retain q values from the older 9/48 or 7/36 or 18/18 families. Original seed scores, sample SDs, descriptors, HTML reports and the model means remain unchanged. Reviewer responses should describe the executed full strategy-pair list and disclose the extension timing. Use completed-action language only once Overleaf changes are applied. Abstract and conclusions are drafts to merge with the live Overleaf and the separate Concern 1/4 work.
''')
    put('INSERTION_GUIDE.md', '''
# Active statistical integration — complete strategy pairs

This package supersedes joint_analysis_final's 9/48 scalar lists. The 162-cell fit and 15 omnibus tests are unchanged, but 14 global and 78 local comparisons now cover every pair of the five strategies. Original results remain versioned and unmodified.

1. Keep the accepted first three statistical paragraphs if already integrated. Replace the last paragraph listing nine/48 tests with the last paragraph of paper/00_statistical_analysis_replacement.tex: all ten strategy pairs, three prompt pairs and the model comparison give 14 global contrasts; the first thirteen within six contexts give 78 local contrasts.
2. Use paper/01_global_sari_table.tex and paper/02_unified_results.tex, not the old nine-row table/q values. The new direct comparisons include every few-shot strategy versus zero-shot and metric/retrieval versus one-shot.
3. Use supplement/00_unified_protocol.tex and 02_local_sari.tex. The copied omnibus and strategy-mean tables are unchanged. Packages longtable/booktabs are required. Original Wilcoxon tables/annotations stay clearly scoped historical supplementary evidence.
4. Update discussion and reviewer responses using DISCUSSION_AND_RESPONSE_GUIDANCE.md. New scalar q values replace earlier values even for shared contrasts; no new model inference or metric scoring occurred.
5. Coordinated abstract/conclusion drafts are in paper/06 and 07. Merge with the actual Overleaf and the separate ablation/penalty findings. Preserve finished Concern 6 edits and the three-selection description. Add no preregistration or equivalence claim.

Reproduction: run_analysis.py --prepare verifies/freezes the plan; --execute verifies the parent fit and computes/verifies the expanded contrast outputs. Full hashes, reconciliation of all 57 shared contrasts and the 10,000 joint bootstrap draws are saved. Local outputs are not automatically pushed to GitHub and the live Overleaf is not edited.
''')
    report = '# Complete strategy-pair unified analysis\n\n14 global contrasts; 78 local contrasts; 15 unchanged omnibus tests. Same model, scores and CR1 covariance as the prior unified analysis. All 57 shared effects, SEs, raw p and intervals verified unchanged. Only scalar BH families expand.\n\n' + glob[['contrast_id','effect','bootstrap_ci_low','bootstrap_ci_high','q_bh']].to_csv(index=False)
    (HERE / 'REPORT.md').write_text(report, encoding='utf-8')
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    (OUT / 'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Built expanded tables, methods, results, discussion guidance and coordinated drafts.')


if __name__ == '__main__':
    main()
