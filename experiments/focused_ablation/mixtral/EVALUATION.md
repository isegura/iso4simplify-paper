# Mixtral evaluation — prepared for manual execution

No full metric evaluation was launched during this preparation.

Preflight passed: all six runs complete with exit code 0; 746 nonempty outputs
aligned by row, ID, source and reference; source/prompt hashes unchanged.
55 outputs reached the 512-token cap (17/30 Cochrane, 1/7 PLABA, 0/0 TSAR,
ISO/ISO+examples respectively). All remain in the primary evaluation.
See verification.json. All nine original Mixtral zero-shot comparators and
their saved aggregate score files are available and aligned.

Run from the repository root:

```powershell
.\experiments\focused_ablation\mixtral\evaluate.ps1
```

This calls `.venv-eval\Scripts\python.exe -u evaluate_mixtral_ablation.py`.
Activation is unnecessary. Progress is printed and saved to a timestamped log
in this directory. Ollama is not used for evaluation; it can be closed to free
GPU memory if still loaded.

Six ablations and nine original Mixtral zero-shot comparators are evaluated
with the same nine metrics as Llama: SARI, corpus BLEU, BERTScore-F1,
MeaningBERT, FKGL, FRE, mean output words, mean compression and mean lexical
copy rate. The earlier MeaningBERT implementation and model hashes are pinned
through the shared focused_metric_runtime.py. TSAR uses both A2/B1 references.
No generation settings, original outputs or metric implementations are changed.

Results are isolated under `mixtral/evaluation/`:

- `ablation_metrics.csv`: six rows with nine metrics.
- `all_metrics.csv`: all 15 evaluated configurations.
- `original_score_check.csv`: 54 original/recomputed metric comparisons;
  historical Mixtral reproduction must be inspected after evaluation, not assumed
  from the earlier Llama validation.
- Per-configuration checkpoint JSONs and descriptive item CSVs.
- `complete.json`: written only after all 15 evaluations finish.

Completed checkpoints are reusable only if input/code/package fingerprints
match. A failed run must be inspected before restarting. Llama results and
scripts are unchanged. The new Python driver intentionally mirrors the Llama
evaluation path, reusing all shared metric functions, with Mixtral paths and
stronger inference-completion/hash checks.

After successful manual evaluation: inspect original-score reproduction,
calculate paired SARI intervals/tests, perform the same prespecified qualitative
review for Mixtral, and update the report to cover both models. None of those
Mixtral results is claimed complete by this preparation.
