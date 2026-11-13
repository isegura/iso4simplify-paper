# Focused organization/summary ablation — preparation only

Status: NOT EXECUTED. Explicit approval is required before any full run.
No result, confidence interval, significance claim or reviewer response is available yet.

## Scope and exact changes

Study the contribution of the explicit organization/initial-summary block in
ISO and ISO+examples, Llama 3.1 8B, zero-shot, three datasets. This does not
identify the complete causal effect of ISO 24495-1.

The two new files in `prompts/` are byte-for-byte copies outside the interval
from `# PRINCIPLES OF ORGANIZATION AND HIERARCHY` up to, excluding,
`# WRITING INSTRUCTIONS (LINGUISTIC LEVEL)`. Both headings in the originals
use one `#`. The removed instructions are equivalent: ISO+examples says
“in the case of processes or instructions” rather than “for processes or
instructions”, and has different blank lines/trailing spaces.
All other instructions and examples, including VISUAL FORMAT, are preserved.
The exact unified diffs are `iso.diff` and `iso_examples.diff`.

`main.py`: add two zero-shot-only prompt mappings, `iso_ablated` and
`iso_examples_ablated`, pointing to the requested filenames. Existing mappings
are unchanged; requesting one/few-shot for an ablated type raises an error.
No generation, preprocessing, postprocessing or metric code is changed.

`run_focused_ablation.py`: safe launcher using main.py, dry-run by default.
It verifies sizes and rowwise ID/source/reference alignment against all three
original zero-shot prompt types. PLABA has 148 rows but 110 unique text IDs;
row position is essential and will be retained in per-item comparisons.
It refuses existing predictions or run records, captures stdout/stderr,
records provenance, elapsed time, completion and truncation counts, and
marks unsuccessful/incomplete runs ineligible for evaluation.
The original main.py also writes its timestamped detailed log in `logs/`.

Created artifacts at this stage: the two prompts, launcher, this document,
two diffs, `inspection.json`, `commands.ps1` and `main_mapping.diff`.
Only the mapping in main.py was edited in existing code. The repository
already contained other modified/deleted/untracked files; those are untouched.

## Verified inputs and original evidence

| Dataset | Test rows | Original prediction directory |
|---|---:|---|
| cochrane | 125 | outputs/llama_512 |
| plaba | 148 | outputs/llama_512 |
| tsar2025 | 100 | outputs/llama_512 |

Test data: `data/<dataset>/<dataset>_test.csv`.
Original predictions: `predictions_llama3_1_8b_<dataset>_<prompt>_zero.csv`,
for minimal, iso and iso_examples. No originals are rewritten.
TSAR evaluation references: `data/tsar2025/tsar2025_test_200.csv`, grouped
with the existing `evaluate_all.load_data_tsar` logic (A2/B1 jointly).
Full verification evidence, original log paths and expanded inference commands
are in `inspection.json`.

## Inference configuration

All six historical ISO/ISO+examples logs in `logs/logs_llama_512` confirm:
Ollama, llama3.1:8b, output limit 512, context 8192, temperature 0,
seed 42, top_k 1, top_p 1, repeat_penalty 1.1, repeat_last_n 64.
Retain num_gpu 999, GPU required, timeout 900 seconds.

Installed model inspected read-only: Q4_K_M, digest
`46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`.
Current Ollama: 0.40.6. Installed model modification date: 2026-03-13.
Historical logs do not establish the historical digest/quantization or
runtime version. Therefore exact historical binary/runtime identity cannot
be certified. No model downloads, settings changes or substitutions are made.
The launcher rejects a model/runtime change since inspection or between runs.

## Execution after approval

The six explicit launcher commands are in `commands.ps1`. Each expands to
main.py with all parameters explicitly specified (see inspection.json).
Run sequentially from the repository using the existing .venv interpreter.
Do not execute the command file until approval. Do not commit or push.

New predictions are isolated in
`experiments/focused_ablation/predictions/llama/` with names such as
`predictions_llama3_1_8b_cochrane_iso_ablated_zero.csv`.
Captured complete logs and per-run JSON records go in this experiment's
`logs/` subdirectory. A failure stops the command file; incomplete files
are retained for inspection and are never silently resumed or evaluated.

## Evaluation plan after generation

Reuse `eval_utils.evaluate_predictions` with `sari_method='standard'`,
semantic evaluation enabled, and the current reference handling. Do not
use the generic filename parser unmodified: it does not recognize ablated
prompt labels. A focused evaluation entrypoint will pass dataset metadata
explicitly and require six complete run records before analysis.

Exact existing implementations:

- SARI: evaluate.load('sari'); current wrapper rounds corpus scores to two
  decimals. No fallback to legacy.
- BLEU: sacrebleu.corpus_bleu, defaults unchanged, corpus scale 0–100,
  with parallel reference streams for TSAR; rounded to two decimals.
- BERTScore-F1: roberta-large, English, rescale_with_baseline=False,
  multi-reference handling delegated to BERTScorer; four decimals.
- MeaningBERT: evaluate.load('davebulaval/meaningbert'), against sources,
  existing item rounding and aggregation retained.
- FKGL and FRE: textstat per output, nanmean, two decimals.

Additional descriptive metrics (only the six ablations and nine original
zero-shot comparators, never all 72 configurations): word count = len(split()),
reusing the existing LEN_PRED convention; compression = output/source word
count, averaged per item. Proposed copy rate = fraction of whitespace-delimited
output tokens whose exact case-sensitive token occurs in the source token set;
punctuation remains attached. This is lexical token overlap, not evidence of
verbatim phrase copying. Empty output copy rate is 0; a zero-length source
has undefined compression, flagged rather than silently divided by zero.
Document this definition consistently for Concern #3 or agree a replacement
before analysis. No text is normalized for the six existing metrics.

Primary endpoint: SARI(ablated) - SARI(original). Use 10,000 paired bootstrap
samples, fixed seed 42, identical row indices for both conditions, recomputing
corpus SARI for each sampled dataset. Use the raw existing SARI metric return
inside resampling (avoid artificial two-decimal CI quantization); retain the
paper wrapper's displayed score scale. Percentile 2.5/97.5 intervals.
Never substitute sentence BLEU means for corpus BLEU. If a paired test is used,
use a two-sided within-item permutation test of the same SARI difference,
with fixed seed and documented count, reporting raw and Holm-adjusted p-values
over six comparisons. Non-significance is not equivalence.

Recompute the nine original zero-shot comparators through the same evaluation
code in new files and check against saved scores_512, flagging discrepancies.
Keep originals unchanged. Include row index as well as ID in per-item CSVs;
include both TSAR references. Keep complementary metrics descriptive.

For qualitative inspection select five equally spaced input positions per
dataset (0, floor((n-1)/4), floor((n-1)/2), floor(3*(n-1)/4), n-1),
the same positions for both prompt families. Inspect paired full texts for
summary-first structure, ordering, grouping, and length; record observations
and evidence without treating subjective judgments as measured rates.
Existing systematic_error_analysis_512 detectors screen format/length/errors,
but do not validate summary quality or information importance.

After approval and successful execution, deliver the nine-metric table,
six SARI comparisons and paired intervals, per-item CSVs, scientific report
and evidence-based draft reviewer response. These do not exist yet.
Interpretation must retain remaining confounding by prompt length, instruction
count, omission permissions and retained formatting requirements.
