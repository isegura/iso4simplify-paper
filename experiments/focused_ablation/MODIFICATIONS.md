# Repository modifications for the focused ablation

## Current Wilcoxon/BH main analysis

Added `analyze_ablation_wilcoxon_bh.py` and
`update_ablation_wilcoxon_documents.py`. The principal tests now use paired
two-sided Wilcoxon and BH, with fixed primary-12/secondary-12 families and
all-24 sensitivity. Per-item two-decimal precision was verified against all
saved original comparators; integer centipoint differences prevent artificial
floating ties. Existing mean effects/bootstrap samples are unchanged. Earlier
permutation/Holm results remain explicit robustness evidence.

New results: `combined/wilcoxon_bh/`. Current reports:
`SCIENTIFIC_REPORT_WILCOXON_BH.md` and
`REVIEWER2_CONCERN1_WILCOXON_BH.md`. Separate LaTeX proposals and tables were
updated and recompiled successfully in the validation project. Superseded proposal sources and the earlier ZIP were removed during the authorized local cleanup. The current package is
`latex_insertions/ablation_latex_wilcoxon_bh.zip`. Neither supplied .tex file
was modified, no generation or metric evaluation was rerun, and no Git commit
or push was made.

## Secondary baseline extension and LaTeX proposals

Added `analyze_ablation_vs_baseline.py` and `prepare_ablation_latex.py`.
Twelve secondary paired SARI comparisons are stored under
`combined/baseline_comparisons/`, with Holm over the secondary 12 and all 24
primary/secondary contrasts, raw bootstrap samples and aligned item files.
`latex_insertions/` contains independent English LaTeX fragments, a Spanish
placement guide and source hashes. The supplied `Downloads/main.tex` and
`Downloads/supplementary_material.tex` were not modified. A separate validation
project is used for any compilation checks. Current Markdown synthesis and
reviewer response include the new baseline results; superseded presentation drafts were removed during the authorized cleanup. No model generation, corpus metric re-evaluation or Git publishing
was performed for this extension.

## Completed Mixtral extension

The shared inference launcher additionally accepts `--model mixtral:latest`,
with default Llama commands unchanged. Mixtral files are isolated under
`experiments/focused_ablation/mixtral/`. New drivers:
`evaluate_mixtral_ablation.py`, `analyze_mixtral_ablation.py`,
`complete_mixtral_ablation_items.py`, and `finalize_two_model_ablation.py`.
They reuse the existing metric functions and the validated earlier MeaningBERT.
The `combined/` directory contains the current two-model report, reviewer draft,
12 comparisons (Holm within model and all 12), 30 aggregate evaluations and
1,492 paired items. Earlier Llama reports/results are retained.
Mixtral adds 30 documented exploratory qualitative comparisons over the same
15 source rows. No new inference settings or original files were changed by
this extension. No manuscript edits or Git publishing have been performed.

## Existing files edited

- `main.py`: two additional zero-shot-only mappings, `iso_ablated` and
  `iso_examples_ablated`. Exact task-specific change: `main_mapping.diff`.
- `.gitignore`: exclude the new local `.venv-eval/` environment.

Pre-existing repository changes and deletions were not reverted or committed.

## New source files

- `prompts/iso_zero_ablated.md`, `prompts/iso_examples_zero_ablated.md`:
  only the designated organization/summary block removed.
- `run_focused_ablation.py`: six-run launcher, alignment checks, provenance,
  completion checks and overwrite protection; dry run unless `--execute`.
- `evaluate_focused_ablation.py`: six ablations plus nine original comparators,
  existing aggregate metric functions and three additional descriptive metrics.
- `focused_metric_runtime.py`: pin and integrity-check the earlier MeaningBERT
  implementation and cached model; applies only to the focused evaluator.
- `verify_meaningbert_original.py`: historical MeaningBERT reproduction check.
- `analyze_focused_ablation.py`: paired SARI bootstrap, randomization tests,
  Holm correction and aligned item SARI comparisons.
- `complete_ablation_items.py`: complete item-level comparison metrics in new
  files; no rewriting inference outputs.
- `finalize_ablation_report.py`: assemble the scientific report and reviewer
  draft from saved results.

## Generated artifacts

Everything below `experiments/focused_ablation/` belongs to the study:

- Preparation, two prompt diffs, command files and inspection evidence.
- Six prediction CSVs in `predictions/llama/`.
- Six complete captured inference logs and six completion JSONs in `logs/`;
  main.py's timestamped detailed logs also remain in the existing root `logs/`.
- Original-score validation, all 15 aggregate evaluations and six ablation
  nine-metric rows in `evaluation/`.
- Statistical comparisons, bootstrap distributions and six paired SARI files
  in `statistics/`.
- Six complete paired item CSVs and consolidated 746-pair file in `per_item/`.
- Thirty qualitative comparisons in `qualitative/`, including a report,
  full side-by-side evidence and case-level observations.
- Scientific report, reviewer response draft, environment/provenance records,
  validation/install/evaluation logs and original-artifact integrity check.

The copied earlier MeaningBERT source in `metric_sources/` is unmodified;
its source, checksum and checkpoint hashes are recorded in provenance.json.
The original model loading code and eval_utils.py remain unchanged.

## Local environment and backup

- Created `.venv-eval/` with official PyTorch 2.10.0+cu128 and the original
  pinned other packages. Original `.venv/` and NVIDIA drivers are unchanged.
- Local backup: `backups/pre-ablation_20261021_160339/`, with ZIP and hash manifest.
  It excludes virtual environments, caches and earlier backups.
- Original-artifact integrity: 289 selected original files match that backup
  byte-for-byte; see `original_artifacts_integrity.json`.

No commits, pushes, releases, tag changes, manuscript edits or external
communications were made. The scientific response is a draft for author review.

## Remaining author decisions

- Review the report and response, then integrate into the actual manuscript
  and supply real section/table numbers. The inspected files did not contain
  the literal RQ1/RQ2 wording, so check terminology before insertion.
- Revisit PLABA shared IDs if stronger uncertainty estimation is required;
  this was explicitly deferred by the user.
- Consider a non-truncated paired sensitivity analysis if needed; it was not
  included in the requested primary ablation analysis and is not claimed done.
- Other reviewer concerns, formal human evaluation and all-72-configuration
  screening remain outside this focused study.
