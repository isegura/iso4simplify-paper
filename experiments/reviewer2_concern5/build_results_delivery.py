"""Build tables and integration prose from the verified retrieval analysis."""
from pathlib import Path
import hashlib
import json
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / 'prepared_retrieval_20261102'
ANALYSIS = PLAN / 'analysis'
OUT = PLAN / 'manuscript_proposals'
PROMPTS = {'minimal': 'Baseline', 'iso': 'ISO', 'iso_examples': 'ISO+examples'}
MODELS = {'llama': 'Llama', 'mixtral': 'Mixtral'}
DATASETS = {'cochrane': 'Cochrane', 'plaba': 'PLABA', 'tsar2025': 'TSAR'}


def write(name, text):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + '\n', encoding='utf-8')


def table(filename, caption, label, columns, headings, rows):
    body = '\n'.join(' & '.join(row) + r' \\' for row in rows)
    write(filename, '\\begingroup\n\\small\n\\setlength{\\tabcolsep}{3pt}\n' +
          '\\begin{longtable}{' + columns + '}\n\\caption{' + caption + '}\\label{' + label + '}\\\\\n\\toprule\n' +
          ' & '.join(headings) + r' \\' + '\n\\midrule\n\\endfirsthead\n\\toprule\n' +
          ' & '.join(headings) + r' \\' + '\n\\midrule\n\\endhead\n' + body + '\n\\bottomrule\n\\end{longtable}\n\\endgroup')


def main():
    proof = json.loads((ANALYSIS / 'verification.json').read_text())
    for name, digest in {**proof['inputs'], **proof['outputs']}.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    d = pd.read_csv(ANALYSIS / 'descriptive_comparisons.csv')
    e = pd.read_csv(ANALYSIS / 'sari_contrasts.csv')
    write('liu2022_retrieval.bib', (HERE / 'manuscript_proposals/liu2022_retrieval.bib').read_text())
    score_rows, metric_rows, contrast_rows = [], [], []
    for (model, dataset, prompt), group in d.groupby(['model', 'dataset', 'prompt'], sort=False):
        g = group.set_index('strategy')
        info = [MODELS[model], DATASETS[dataset], PROMPTS[prompt]]
        mean = g.loc['few_random_mean']
        score_rows.append(info + [f'{g.loc["few_metric", "SARI"]:.2f}', f'{mean.SARI:.2f} $\\pm$ {mean.SARI_sd:.2f}', f'{g.loc["few_retrieval", "SARI"]:.2f}'])
        r = g.loc['few_retrieval']
        metric_rows.append(info + [f'{r[k]:.2f}' if k != 'BERTScore-F1' else f'{r[k]:.4f}' for k in ['SARI', 'BLEU', 'BERTScore-F1', 'MeaningBERT', 'FKGL', 'FRE']])
    for r in e.itertuples():
        q = '$<0.001$' if r.q_bh < .001 else f'{r.q_bh:.3f}'
        contrast_rows.append([MODELS[r.model], DATASETS[r.dataset], PROMPTS[r.prompt], 'Metric' if r.family == 'retrieval_minus_metric' else 'Mean random',
                              f'{r.effect:+.2f}', f'[{r.bootstrap_ci_low:+.2f}, {r.bootstrap_ci_high:+.2f}]', q])
    table('supplement/01_sari_comparison.tex',
          'SARI for three-demonstration selection strategies. Random values are the mean and sample standard deviation across fixed selections 42, 44 and 46; the SD is not a confidence interval. All response instances are retained. No significance annotations from the original tables are transferred to these values.',
          'tab:retrieval_sari_comparison', 'lllrrr', ['Model', 'Dataset', 'Prompt', 'Metric', 'Random mean $\\pm$ SD', 'Retrieval'], score_rows)
    table('supplement/02_retrieval_metrics.tex',
          'Automatic metrics for retrieval (18 configurations, 2,238 response instances). BLEU is corpus BLEU, BERTScore is reference-based F1, and MeaningBERT compares output with source. No new inferential tests are performed for metrics other than SARI.',
          'tab:retrieval_metrics', 'lllrrrrrr', ['Model', 'Dataset', 'Prompt', 'SARI', 'BLEU', 'BERTScore', 'MeaningBERT', 'FKGL', 'FRE'], metric_rows)
    table('supplement/03_sari_contrasts.tex',
          'Paired SARI differences: retrieval minus comparator. Random is averaged within each response instance across the three fixed selections. Intervals are pointwise 95\\% document-group bootstrap intervals (10,000 draws); $q$ values are from conditional cluster-robust cell-means contrasts with BH adjustment separately within each family of 18 contrasts. An interval excluding zero need not imply $q<0.05$.',
          'tab:retrieval_sari_contrasts', 'llllrrr', ['Model', 'Dataset', 'Prompt', 'Comparator', '$\\Delta$ SARI', '95\\% bootstrap CI', '$q_{BH}$'], contrast_rows)
    base = pd.read_csv(PLAN / 'evaluation/summaries/all_models_all_datasets.csv')
    desc_rows = []
    for r in base.itertuples():
        desc_rows.append([MODELS[r.model], DATASETS[r.dataset], PROMPTS[r.prompt], str(r.n), f'{r.mean_LEN_PRED:.1f}', f'{r.mean_compression_ratio:.3f}', f'{r.mean_copy_rate:.3f}', str(r.empty_n), str(r.capped_n)])
    table('supplement/04_descriptors.tex',
          'Retrieval output descriptors. Compression and lexical copy are means of per-instance ratios, not ratios of aggregate lengths; lexical copy is token overlap with the source, not a measure of factual fidelity. Cap indicates termination by the 512-token limit. The empty output is retained.',
          'tab:retrieval_descriptors', 'lllrrrrrr', ['Model', 'Dataset', 'Prompt', '$n$', 'Words', 'Compression', 'Copy', 'Empty', 'Cap'], desc_rows)
    write('paper/01_retrieval_methods.tex', r'''
\subsection{Input-Conditioned Demonstration Retrieval}
As an additional three-demonstration few-shot comparison, we retrieve training examples separately for each target source text using cosine similarity between source-text embeddings. The encoder is \texttt{all-MiniLM-L6-v2}; test references, generated outputs and simplification scores are not used for selection. The procedure follows the general idea of input-conditioned retrieval discussed by \cite{liu-etal-2022-makes}, with an explicit context constraint rather than an exact reproduction of that method. Each target receives the same three complete demonstrations across the two models and three prompt families. We select the eligible triple maximizing the sum of source similarities subject to all six complete prompts fitting 7,616 input tokens, reserving 512 output tokens and 64 additional tokens within an 8,192-token context. Neither texts nor demonstrations are trimmed.

The training pool excludes exact normalized matches to test sources and matching target document identifiers, and demonstrations have distinct source texts and document identifiers. For TSAR, one reference is assigned to each of its 20 training sources using a fixed assignment seed of 42, with 10 A2 and 10 B1 references in the candidate pool. This assignment is shared across prompts and models; no CEFR quota is imposed per target and no target CEFR level is requested. We generate 18 full-test configurations (2,238 response instances), retaining empty and token-capped outputs. Runtime details and complete selection rules are documented in the supplementary material.

The prespecified primary SARI comparisons are retrieval minus the fixed metric-selected comparator in each of the 18 matched model--dataset--prompt settings. Secondary comparisons use the mean of random selections 42, 44 and 46 within each response instance. We use the conditional cell-means analysis with uncertainty grouped by dataset and source identifier, preserving repeated PLABA identifiers. We report pointwise 95\% document-group bootstrap intervals (10,000 draws, seed 20261023) and cluster-robust contrast tests, with Benjamini--Hochberg adjustment separately for the two families of 18 contrasts. The other metrics and output descriptors are descriptive. This historical comparison does not isolate a causal effect of retrieval independently of demonstration content, reference assignment or runtime differences.
''')
    write('paper/02_retrieval_results.tex', r'''
\subsection{Input-Conditioned Retrieval Results}
Retrieval has higher mean SARI in 11 of 18 settings relative to the fixed metric-selected comparator and in 11 of 18 relative to the mean of the three fixed random selections. These are descriptive counts of related configurations, not independent replications or tests of overall superiority. After adjustment within each contrast family, retrieval exceeds the metric-selected comparator for Llama Baseline on Cochrane ($\Delta=1.06$), Llama Baseline and ISO+examples on PLABA ($\Delta=1.90$ and $1.81$), and Mixtral ISO on PLABA ($\Delta=2.54$). It is lower for Llama ISO+examples on TSAR ($\Delta=-1.44$). Relative to mean random, the detectable contrasts are an increase for Llama Baseline on Cochrane ($\Delta=1.03$) and a decrease for Llama ISO+examples on TSAR ($\Delta=-1.58$). No other contrast has $q<0.05$; these results do not establish equivalence in the remaining settings. Tables in the supplementary retrieval section give all scores, intervals and adjusted values.

All 2,238 expected retrieval outputs were evaluated. Observed input-token counts matched the complete-prompt preflight counts in every case. Llama had 22 token-limit terminations; Mixtral had 28 and one empty output, with all cases retained. The accompanying HTML reports expose every output and, separately, the 15 lowest-SARI response instances per configuration for illustrative inspection. Screening indicators are not confirmed error rates or evidence of ISO compliance.
''')
    write('paper/03_RQ4_addition.tex', r'''
The input-conditioned retrieval comparison further qualifies any ranking of demonstration-selection methods. Although retrieval has higher SARI than each comparator in 11 of the 18 evaluated configurations, its adjusted differences vary by model, dataset and prompt: four increases and one decrease are detectable against the fixed metric-selected heuristic, whereas one increase and one decrease are detectable against mean random. Similarity-based retrieval therefore offers gains in some tested settings without a consistent advantage over the evaluated random selections. These comparisons concern this encoder, three-example budget, reference policy and historical controls; they do not establish a general ordering of random, metric-based and retrieval selection.
''')
    write('paper/04_limitations_replacement.tex', r'''
The retrieval experiment is limited to one source-text encoder, three complete demonstrations, and a context-constrained selection rule. The shared budget constraint can change the selected sources relative to unconstrained nearest-neighbor retrieval, and the TSAR training-reference assignment is fixed and balanced only at the candidate-pool level. The random controls comprise three constrained fixed selections rather than a sample sufficient to establish robustness over all demonstration sets. Comparisons also use historical controls and can reflect differences in demonstration content, reference choices and runtime; they do not isolate retrieval as a single causal factor. No retrieval one-shot condition, alternative retrieval encoder or CEFR-controlled generation is evaluated. Non-significant contrasts do not demonstrate equivalence.
''')
    write('paper/05_future_work_replacement.tex', r'''
Future work should evaluate alternative retrieval encoders and context budgets, vary the number of complete demonstrations, and examine sensitivity to training-reference assignment under matched contemporary executions. Reader-centered evaluation and explicit CEFR-controlled generation would address questions not resolved by the automatic metrics used here.
''')
    write('supplement/00_retrieval_protocol.tex', r'''
\section{Input-Conditioned Retrieval: Protocol and Results}
The frozen local analysis plan was finalized before retrieval generation; it is not an external preregistration. Source embeddings use the cached \texttt{all-MiniLM-L6-v2} checkpoint \texttt{1110a243fdf4706b3f48f1d95db1a4f5529b4d41}. Long sources are split into non-overlapping 224-token chunks without truncation; each decoded and re-encoded chunk must fit the encoder's 256-token limit. Unit chunk vectors are pooled using token-length weights and normalized again. Original complete source/reference pairs are inserted into generation prompts.

Pool normalization uses Unicode NFKC, case folding and whitespace collapse. Duplicate sources are collapsed; exact normalized test-source matches and matching target document identifiers are excluded. An eligible triple has distinct sources and document identifiers. Triples are searched best-first by summed cosine similarity, with deterministic training-row ties. The first feasible triple maximizes the stored float64 similarity objective under the exact prompt budget. Feasibility requires all combinations of the two models and three prompt families to fit 7,616 input tokens; 512 output tokens and a 64-token margin are reserved in the 8,192-token context. A 5,000-triple search guard stops rather than silently changes the procedure; no query reached the guard. Demonstrations are ordered by decreasing similarity and shared across all six combinations for each target. Sources are not trimmed and the nearest one or two examples are not forcibly retained when choosing a feasible triple.

For TSAR, the 20 training-source identifiers are sorted and permuted using NumPy PCG64 with reference-assignment seed 42. Ten receive their A2 reference and ten their B1 reference. This assignment remains fixed across all target texts, prompts and models and is distinct from the generation seed. In the 300 selected demonstration occurrences, 168 references are A2 and 132 B1; the 10/10 balance applies to the pool, not to each prompt or to selected occurrences. Outputs have no requested CEFR level. Both test references are used jointly for reference-based evaluation.

Generation uses temperature 0, seed 42, top\_k 1, top\_p 1, repeat penalty 1.1, repeat\_last\_n 64, 512 maximum output tokens and an 8,192-token context. Runtime metadata record Ollama 0.40.13 for these new generations; the original manuscript's historical runtime must not be silently attributed to them. The installed model digests, templates and native tokenizer are pinned by the execution manifest. Every observed prompt-token count matches its preflight value (2,238 checks), and no context warning was recorded. Completion certificates and prediction hashes are verified before evaluation. The nine-row pilots remain in the complete datasets. A total of 50 outputs terminate at the generation limit, and one Mixtral PLABA ISO+examples output is empty (source identifier 28665969, observed termination \texttt{stop}); none are removed or regenerated.

SARI, reference-based BERTScore-F1, corpus BLEU, source-based MeaningBERT, FKGL and FRE use the existing validated evaluation implementations and rounding. For the historical metric-selected comparator, item scores are verified against the original audit and corpus BLEU is recomputed from saved strings using SacreBLEU's default 13a protocol; sentence BLEU is not averaged. The random descriptive summaries are the mean and sample SD of the three per-selection scores, including the mean of three corpus BLEU scores, rather than pooling predictions into a larger corpus. Output-word counts, compression and lexical copy follow the Concern 3 definitions.

The 36 paired SARI contrasts use dataset/source-identifier grouping (335 groups across datasets), preserving repeated PLABA identifiers. The random score is averaged within each response instance across selections 42, 44 and 46 before comparison. Conditional cell-means regression uses finite-sample-corrected cluster-robust covariance and $t$ tests with the relevant dataset's number of groups minus one degrees of freedom. Stratified document-group bootstrap resamples all configurations jointly within dataset (10,000 draws, seed 20261023). Confidence intervals are pointwise; BH-adjusted test values are computed separately for the 18 retrieval-minus-metric and 18 retrieval-minus-mean-random contrasts. Confidence-interval exclusion of zero and adjusted significance are different criteria. Other metrics are descriptive; no pooled overall retrieval test or post-hoc inferential metric family is added.
''')
    abstract = (ROOT / 'experiments/reviewer2_concern2/manuscript_proposals/paper/00_abstract_replacement.tex').read_text().strip()
    abstract = abstract.replace('a metric-selected few-shot set is retained as a fixed comparator.', 'a metric-selected few-shot set is retained as a fixed comparator, and an additional experiment evaluates input-conditioned retrieval of three complete demonstrations under a shared context constraint.')
    abstract = abstract.replace('Demonstration choice can materially affect scores,', 'Retrieval yields configuration-dependent SARI changes, with one increase and one decrease detectable relative to mean random after multiplicity adjustment, rather than a consistent advantage. Demonstration choice can materially affect scores,')
    write('paper/06_abstract_coordinated_draft.tex', abstract)
    conclusion = (ROOT / 'experiments/reviewer2_concern2/manuscript_proposals/paper/11_conclusion_replacement.tex').read_text().strip()
    conclusion = conclusion.replace('These comparative findings', 'Input-conditioned retrieval adds a complementary comparison: after separate multiplicity adjustment, four SARI increases and one decrease are detectable relative to the fixed metric-selected comparator, and one increase and one decrease relative to mean random. Its benefit is configuration-dependent under the tested three-example context constraint and does not establish a general ordering of selection methods.\n\nThese comparative findings')
    write('paper/07_conclusions_coordinated_draft.tex', conclusion)
    write('paper/08_error_analysis_addition.tex', r'''
The retrieval outputs are accompanied by complete HTML inspection reports and separate 15-lowest-SARI reports for each of the 18 configurations (270 selected response instances). This selection provides illustrative low-scoring cases rather than a representative estimate of errors. The transparent automatic screening rules used for the original outputs are also applied separately to retrieval; candidate indicators can have false positives and are not pooled with the original 72-configuration denominators. Token-limit termination and an empty response are reported as execution outcomes, not automatically classified as semantic errors. A systematic human evaluation or validated comparison of error rates is not claimed.
''')
    write('REVIEWER2_CONCERN5_RESPONSE.md', '''
# Reviewer 2, Concern 5 — completed retrieval experiment

**Status:** experiment, evaluation and planned comparisons completed locally; manuscript edits below are prepared for integration. The past-tense author response is suitable only after the corresponding changes have actually been applied and checked in Overleaf. Add final page/line references after compilation. This replaces the earlier response declining the retrieval experiment.

## Author response — use after integration

We thank the reviewer for suggesting input-conditioned demonstration retrieval. We have added a focused comparison using the two existing models, three datasets and three prompt families, with three complete demonstrations per target (18 configurations and 2,238 response instances). Retrieval uses source-text cosine similarity with all-MiniLM-L6-v2; test references and output scores do not enter selection. For each target, the selected triple maximizes summed similarity subject to a shared exact context constraint across both models and all three prompts. We reserve 512 output tokens and 64 additional tokens within an 8,192-token context, retain complete demonstrations, and verify observed input-token counts against preflight counts for every generation. The supplementary protocol documents chunking, exclusion rules, the fixed balanced TSAR training-reference assignment, runtime provenance and all retained outputs, including capped and empty responses.

We clarify that the original metric-selected comparator is one fixed set per dataset. Its source/reference similarity and overlap are distinct from similarity to the current input, while FRE gain is a surface readability indicator, not a guarantee of comprehension or meaning preservation. We describe the new retrieval experiment as an adaptation of the input-conditioned retrieval idea rather than an exact reproduction of Liu et al. (2022).

The planned primary comparisons contrast retrieval with the fixed metric-selected comparator in 18 matched settings; secondary comparisons use the mean of random selections 42, 44 and 46 within each response instance. We report document-group bootstrap intervals and conditional cluster-robust SARI contrast tests, adjusting separately for the two families of 18 tests. Retrieval has higher mean SARI in 11 of 18 settings against each comparator. After adjustment, four increases and one decrease are detectable against metric selection. Against mean random, the detectable contrasts are an increase for Llama Baseline on Cochrane (1.03 SARI points) and a decrease for Llama ISO+examples on TSAR (1.58 points). The remaining comparisons do not establish equivalence. All six automatic metrics and output descriptors are reported; only SARI receives these new inferential tests.

We have revised the selection discussion, abstract, conclusions and limitations to reflect this configuration-dependent evidence. The results do not support a general ranking of retrieval, random selection and the evaluated fixed metric heuristic. The comparisons retain historical controls and are conditional on the chosen encoder, context budget, demonstration/reference choices and runtime; they do not isolate a causal effect of retrieval. Full-output and low-SARI HTML reports are supplied as inspection artifacts, without claiming human evaluation or confirmed error rates.

## Author action — use after integration

We clarified the original fixed-set heuristic in the demonstration-selection methods, added the input-conditioned retrieval protocol and planned statistical comparisons, added results and supplementary tables covering all 18 settings, extended the output-inspection artifacts, and revised the selection discussion, limitations, abstract, conclusions and future work. Final locations and page/line references must be filled in after integration. No new one-shot retrieval, third model, human study or general ISO-compliance claim is introduced.
''')
    write('INSERTION_GUIDE.md', '''
# Concern 5 — integration of completed retrieval results

This is the active guide. The old `experiments/reviewer2_concern5/manuscript_proposals` directory describes a superseded no-retrieval alternative. Its two original-selector clarification fragments remain useful, but its missing-retrieval abstract/limitations/conclusions/future-work text must not be applied.

The current Overleaf source has manual Concern 6 edits after the received ZIP. These are replacement/insertion units, not a patch against that stale ZIP. No original Overleaf source was edited here. Apply changes with `\\rev{}` at paragraph level if required; do not wrap entire longtables in a highlight command.

1. **Methods, demonstration selection:** retain the original thresholds, weights and diversity rule. Use the old `00_fixed_selector_method.tex`, `01_FRE_definition_replacement.tex` and `02_similarity_interpretation_replacement.tex` to clarify the fixed-set selector if still needed. Add `paper/01_retrieval_methods.tex` alongside demonstration-selection/statistical methods; separate it from the original 72-configuration historical tests and Concern 2's joint analysis. Avoid repeating their shared statistical definitions.
2. **Results:** insert `paper/02_retrieval_results.tex` after the three-selection results and before Error Analysis. Preserve original scores and their historical annotations. Add a reference to the supplementary retrieval section by its final section number; do not use cross-document `\\ref` without external-reference support.
3. **Supplement:** add `supplement/00_retrieval_protocol.tex`, followed by tables 01–04. Load `longtable` and `booktabs` if needed. Tables include all 18 selection comparisons, 18 six-metric retrieval configurations, all 36 SARI contrasts, and 18 descriptor rows. Keep article/supplement labels unique. Use final section numbering, avoiding conflicts with Concerns 1/4/7. The received ZIP lacks the key `liu-etal-2022-makes`: merge `liu2022_retrieval.bib` into the current `biblio.bib` if the key is still absent, then compile with BibTeX as usual.
4. **RQ4 / selection discussion:** preserve the verified Concern 2 results and append `paper/03_RQ4_addition.tex`. Replace assertions that retrieval was not evaluated. Do not transfer the random-vs-metric overall contrast to retrieval or claim a new pooled retrieval test.
5. **Error Analysis / Concern 7:** use `paper/08_error_analysis_addition.tex` and the separate HTML index. Keep original 8,952-response screening denominators distinct from the 2,238 retrieval responses. No human error-rate claims can be inferred from the screening tables.
6. **Limitations and future work:** replace old 'no retrieval experiment' paragraphs with `paper/04_limitations_replacement.tex` and `paper/05_future_work_replacement.tex`; merge overlapping scope language with Concern 6. Keep alternative encoders/budgets as future work rather than proposing the experiment already completed here.
7. **Abstract/conclusions:** `paper/06_abstract_coordinated_draft.tex` and `paper/07_conclusions_coordinated_draft.tex` extend the verified Concern 2/3/6 drafts with the new selection results. Review them against the actual Overleaf text and Alberto's Concern 1 before replacing shared paragraphs. They are coordinated drafts, not a claim that all concerns have been integrated. Preserve the accepted two-instruction-tuned-model title and concise Concern 6 model-scope sentence.
8. **Reviewer response:** use `REVIEWER2_CONCERN5_RESPONSE.md` only after integration; add final page/line references. It supersedes the old response saying retrieval was not run.

## Artifacts and reproduction

- Analysis: `../analysis/descriptive_comparisons.csv` and `sari_contrasts.csv`.
- HTML index: `../analysis/error_analysis/index.html` (36 reports: 18 complete, 18 lowest-15; 270 selected response instances).
- Complete evaluation: `../evaluation/summaries/all_models_all_datasets.csv`.
- Reproduce/verify analysis: `.\\.venv\\Scripts\\python.exe experiments/reviewer2_concern5/analyze_prepared_results.py`.
- Rebuild these tables/texts: `.\\.venv\\Scripts\\python.exe experiments/reviewer2_concern5/build_results_delivery.py`.
- Analysis integrity: `../analysis/verification.json`; delivery integrity and QA are recorded separately.

No predictions, original metric results, Concern 1/4 work, historical statistical plans, or Overleaf files are overwritten. Repository publication/upload is a separate action; this local delivery does not imply a GitHub push. The final combined IEEE project still requires compilation and review in Overleaf.
''')
    write('README.md', '''
# Retrieval results ready for manuscript integration

Start with [INSERTION_GUIDE.md](INSERTION_GUIDE.md). The evaluation and planned comparisons are complete. The response and manuscript text are ready for review, not already integrated in Overleaf.

Four BH-significant SARI increases and one decrease are observed against the fixed metric comparator; one increase and one decrease against mean random. The main conclusion is configuration dependence, not general superiority. Full details and pointwise intervals are in the CSVs and supplementary tables.

The old no-retrieval route is superseded. Do not edit or erase frozen historical input manifests to make their original status fields describe the completed study; current status is documented separately.
''')
    report = '''# Retrieval — completed results and limitations\n\n18 configurations and 2,238 outputs are certified and evaluated. No observed/preflight input-token mismatch exists. Llama has 22 capped responses; Mixtral has 28 plus one empty response. All are retained.\n\n## Comparisons\n\nRetrieval exceeds each comparator descriptively in 11/18 cells. Against metric selection: four adjusted positive and one adjusted negative SARI contrasts. Against mean random: one positive (Llama Baseline/Cochrane, +1.0325) and one negative (Llama ISO+examples/TSAR, -1.5820). Remaining adjusted contrasts are not evidence of equivalence. Pointwise bootstrap intervals can exclude zero when adjusted q is above .05; use q for the planned significance decision.\n\n## Screening scope\n\n36 HTML reports cover all 2,238 outputs and the 15 lowest-SARI instances in each configuration (270 illustrative instances). Transparent rules are reused from Concern 7 without claiming detector validation, human evaluation, or semantic-error prevalence. Separate candidate counts:\n\n'''
    flags = pd.read_csv(ANALYSIS / 'error_analysis/screening_candidates.csv')
    for col in flags.select_dtypes('bool'):
        report += f'- {col}: {int(flags[col].sum())}/2238.\n'
    report += '\nIndicators can overlap. List markers/acronyms are not intrinsically errors; no-terminal-punctuation candidates are not automatically truncations. The low-SARI sample is selected after scoring for inspection, not used to choose the retrieval procedure or the inferential family.\n\n## Historical-control limits\n\nOne encoder, a shared context-constrained triple, and a fixed TSAR training-reference policy are evaluated. Controls are historical and cannot identify a pure causal retrieval effect. No general ranking, human comprehension benefit, CEFR control, or comprehensive ISO compliance follows.\n'
    (ANALYSIS / 'REPORT.md').write_text(report, encoding='utf-8')
    (ANALYSIS / 'METHODOLOGY.md').write_text('''# Reproducible planned comparison\n\nThe frozen active protocol is ../ANALYSIS_PLAN.md (2 November preparation); older parent-folder plans are historical. Primary family: 18 paired retrieval-minus-few-metric SARI contrasts. Secondary family: 18 paired retrieval-minus-mean-random contrasts. Mean random averages selections 42/44/46 within each row. The 335 dataset/source-ID groups preserve shared PLABA IDs. The existing Concern 2 finite-sample-corrected clustered cell-means core is reused with 54 observed cells (18 settings × retrieval, fixed metric, mean random). Tests use dataset group count minus one degrees of freedom. BH is separate per 18-test family. Bootstrap jointly resamples document groups within dataset, 10,000 draws, seed 20261023. Intervals are pointwise, not multiplicity-adjusted. No post-hoc overall contrast or inference on other metrics is added.\n\nAll retrieval certificates, evaluation item hashes, input hashes, row alignments and reference arrays are checked. Historical fixed CSVs match the original statistics audit; random evaluations match their saved input/item hashes. Corpus BLEU is computed from fixed saved predictions with SacreBLEU defaults, not averaged item BLEU; random BLEU is a descriptive mean of three corpus scores. No model inference, semantic reevaluation, prediction editing or output exclusion is performed. Complete input/output hashes and bootstrap sufficient statistics/draws are retained in verification.json and bootstrap_draws.npz.\n''', encoding='utf-8')
    delivery = dict(status='prepared_not_integrated', analysis_verification_sha256=hashlib.sha256((ANALYSIS / 'verification.json').read_bytes()).hexdigest(),
                    files={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name != 'delivery_manifest.json'})
    (OUT / 'delivery_manifest.json').write_text(json.dumps(delivery, indent=2), encoding='utf-8')
    print('Built', len(delivery['files']), 'delivery files:', OUT)


if __name__ == '__main__':
    main()
