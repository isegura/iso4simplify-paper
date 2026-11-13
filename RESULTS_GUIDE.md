# Results and artifact map

## Main study

| Material | Location |
| --- | --- |
| Current six-metric results for all 90 strategy cells (means/SDs in long form) | `results/main_metrics_full_precision.csv` |
| Original 72 prediction files | `outputs/llama_512/`, `outputs/mixtral_512/` |
| Additional 72 prediction files | `experiments/reviewer2_concern2/predictions/{model}/seed_{44,46}/` |
| Random-condition item metrics and corpus BLEU | `experiments/reviewer2_concern2/evaluation/metrics/` |
| Retrieval 18 prediction files and item metrics | `experiments/reviewer2_concern5/prepared_retrieval_20261102/predictions/`, `evaluation/` |
| Retrieval selected demonstrations, reference assignment and token counts | Same retrieval folder: `selected_examples.csv`, `tsar_reference_assignment.csv`, `token_counts.csv` |
| Current global/local SARI contrasts | `experiments/joint_analysis_all_pairs/results/global_sari.csv`, `local_sari.csv` |
| Joint-model fit, covariance and Wald tests | `experiments/joint_analysis_final/results/` (parent-fit dependency; scalar contrasts there are superseded by the all-pairs folder) |
| Output descriptors, 162 runs and 90 mean/SD rows | `experiments/reviewer2_concern3/integration_20261112/` |
| Input lengths and generation-limit audit | `experiments/reviewer2_concern4/updated_scope_20261110/` |
| Automatic screening, all 20,142 outputs | `experiments/reviewer2_concern7/integration_20261112/` |
| Figure and plotted SARI data | `experiments/reviewer2_concern11/output/pdf/` |
| Full outputs and lowest-15-SARI reports | `experiments/html_reports_20261113/reports/index.html` |

## Separate supporting experiments

- Organization/summary ablation: `experiments/focused_ablation/combined/`; current primary and secondary tests are under `combined/wilcoxon_bh/`. Model-specific raw outputs, per-item scores and earlier permutation/Holm robustness evidence are preserved in the same experiment tree.
- Repetition-penalty diagnostic: `experiments/reviewer2_concern4/repeat_penalty/cochrane_iso_shared_subset/`. The diagnostic compares selected existing penalty-1.1 outputs against penalty-1.0 reruns. It is not representative of full-test-set failure frequencies or overall quality.
- Original qualitative error-analysis evidence: `error_analysis_candidates_512/`. These historical selections use the original experiment set. The new complete reports do not redefine the paper's qualitative sample or introduce new qualitative judgments.

The released five item-level metrics exclude BLEU: corpus BLEU is stored with run-level evaluation summaries. The two TSAR references are used jointly where required. Never average sentence BLEU values to reconstruct corpus BLEU.
