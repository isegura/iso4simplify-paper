# Separate evaluation environment

Created `.venv-eval` without changing `.venv` or NVIDIA drivers.
Installed official PyTorch 2.10.0+cu128 wheel from download.pytorch.org.
All other packages are pinned to the versions captured from `.venv`.
`pip check`: no broken requirements.

Validated on the NVIDIA GeForce RTX 5080 Laptop GPU:

- CUDA 12.8 available; real matrix multiplication passed.
- BERTScore roberta-large loaded and ran on CUDA; identical-pair smoke score 1.0.
- Earlier cached MeaningBERT implementation loaded its existing root checkpoint
  and computed a non-identical-pair score successfully. No model download was needed.
- MeaningBERT's earlier implementation uses CPU; GPU acceleration was not added
  to that implementation. This preserves its code during historical validation.

Environment inventories: `environment_original.txt`, `environment_eval.txt`.
Validation: `environment_eval_validation.json`, `environment_eval_smoke.log`.
The only intentional package change is the CPU-to-CUDA build of torch 2.10.0.
`pip freeze` records the CUDA wheel as a direct URL rather than an == entry.

Important reproducibility finding: the newest cached MeaningBERT metric module
changes its default checkpoint to a `large` subfolder. Do not use an unpinned
`evaluate.load('davebulaval/meaningbert')` for manuscript comparisons.
An unmodified earlier cached module is copied under
`metric_sources/meaningbert_original/meaningbert_original.py`; provenance and
SHA-256 are recorded in `metric_sources/provenance.json`.
The focused evaluator now explicitly loads this module via
`focused_metric_runtime.py`. Its module hash, cached checkpoint revision,
configuration and weights hashes are verified before loading; offline mode
prevents resolving newer remote versions. The shared eval_utils.py is unchanged.

Historical validation PASSED on all nine original Llama zero-shot configurations
(minimal, ISO, ISO+examples for Cochrane, PLABA and TSAR2025). MeaningBERT matches
the saved scores exactly at their reported two-decimal precision in all nine
cases. See `meaningbert_validation/original_scores.csv` and `verification.json`.
This validates MeaningBERT only, not the other five existing metrics.
The earlier full evaluation attempt did not produce completed metrics.

Use the environment directly, without activation:

```powershell
.\.venv-eval\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

No full evaluation was launched as part of environment setup. No predictions,
original metrics, original environment packages, commits or tags were changed.

## Manual full evaluation

From the project root, run:

```powershell
.\experiments\focused_ablation\evaluate.ps1
```

This invokes `.venv-eval\Scripts\python.exe -u evaluate_focused_ablation.py`,
shows progress and saves a timestamped log. It computes the nine metrics for
the six ablations and nine original zero-shot comparators, writes only under
`experiments/focused_ablation/evaluation/`, and reuses completed checkpoints
only when input, code and dependency fingerprints match. A failed run must be
inspected before restarting. `complete.json` signals all 15 evaluations finished.
Confidence intervals and qualitative analysis are separate subsequent steps.
