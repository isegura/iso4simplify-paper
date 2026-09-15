# iso4simplify

This repository contains the code and results for the paper *ISO-Based and Minimal Prompting for Text Simplification: An Empirical Evaluation with Large Language Models*, submitted to IEEE Access.

The project evaluates ISO 24495-1-based prompting strategies for text simplification with instruction-tuned large language models.

The project compares `minimal`, `iso`, and `iso_examples` prompts across three datasets (`cochrane`, `plaba`, and `tsar2025`) using `zero`, `one`, and `few` prompting strategies. In few-shot settings, examples can be selected using either `random` or `metric` sampling.

## Structure

- `data/`: input datasets; see redistribution notes below.
- `prompts/`: prompt templates loaded by `main.py`.
- `outputs/llama_512/` and `outputs/mixtral_512/`: final predictions with a 512-token generation limit (36 prediction CSVs per model).
- `scores_512/`: aggregate evaluation scores for the final predictions.
- `outputs/truncation_audit_512_all_experiments.csv`: truncation audit.
- `error_analysis_candidates_512/`: JSON, HTML, and supporting analysis files.

## Paper Configuration

The Ollama runs use `llama3.1:8b` and `mixtral:latest`. Recorded decoding
parameters are temperature 0, top-k 1, top-p 1.0, seed 42, repeat penalty 1.1,
and repeat-last-n 64. The generation limit is 512 tokens and the context window
is 8192 tokens. These settings are defined in `main.py` and passed to Ollama by
`model_utils.py`.

The experiments were run locally with Ollama v0.23.1 on a Windows 11 laptop
equipped with an NVIDIA GeForce RTX 4080 Laptop GPU and 32 GB of RAM.

Zero-shot, one-shot, and few-shot use 0, 1, and 3 demonstrations, respectively.
`ISO+examples` additionally contains illustrative examples of plain-language
principles; these are distinct from the input-output demonstrations.

The installed model metadata reports Q4_K_M for Llama and Q4_0 for Mixtral.
Q4_0 is also recorded in a saved Mixtral diagnostic. Historical Llama
quantization has not been verified from run metadata. Model tags can change
and may resolve to different model versions over time.

Inference calls use the local Ollama API. Leading and trailing whitespace is
removed from responses; introductory phrases, explanatory notes, and prompt
labels are not stripped. Fixed decoding parameters do not guarantee identical
outputs across different software versions or hardware.

## Installation

On Windows, from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements_windows.txt
```

For Hugging Face models that require authentication, define `HF_TOKEN` in the environment. To use Ollama, make sure the Ollama server is running at `localhost:11434` and that the target model is available locally.

Ollama must be installed separately; it is not included in
`requirements_windows.txt`. Metric models and dependencies may require
downloads on first use.

## Running An Experiment

The main script is `main.py`. It generates simplifications and saves predictions incrementally in the directory specified by `--outputs_dir`.

Example with Ollama and Mixtral, writing to a separate rerun directory:

```powershell
python main.py --backend ollama --model mixtral:latest --dataset cochrane --type_prompt iso_examples --strategy few --sampling_method metric --max_new_tokens 512 --ollama_num_ctx 8192 --ollama_temperature 0 --ollama_top_k 1 --ollama_top_p 1.0 --ollama_seed 42 --ollama_repeat_penalty 1.1 --ollama_repeat_last_n 64 --ollama_timeout 900 --outputs_dir reruns
```

For the paper's other model, replace `mixtral:latest` with `llama3.1:8b`.
Keep `--backend ollama`: the optional Hugging Face backend uses different
generation settings and is not a substitute for the reported Ollama runs.

`run_all_dataset.py` selects both paper models and writes new predictions to
`reruns/`, separate from the final artifacts. This batch script
skips existing prediction files; `main.py` can overwrite the matching output.

Main arguments:

- `--backend`: `hf` or `ollama`.
- `--model`: model name.
- `--dataset`: `cochrane`, `plaba`, or `tsar2025`.
- `--type_prompt`: `minimal`, `iso`, or `iso_examples`.
- `--strategy`: `zero`, `one`, or `few`.
- `--sampling_method`: `random` or `metric`; only used with `few`.
- `--head`: limits the number of examples for quick tests.
- `--ollama_timeout`: timeout for Ollama requests.

Output files follow this convention:

```text
<output_root>/<model_family>/predictions_<model>_<dataset>_<prompt>_<strategy>.csv
<output_root>/<model_family>/predictions_<model>_<dataset>_<prompt>_few_<sampling>.csv
```

## Evaluating Predictions

`evaluate_all.py` computes BLEU, SARI, FKGL, FRE, BERTScore-F1, and MeaningBERT.
The following commands evaluate each final prediction directory separately and
write to a new directory, leaving `scores_512/` untouched:

```powershell
python evaluate_all.py --predictions_dir outputs/llama_512 --scores_dir scores_recomputed/llama_512 --sari_method standard
python evaluate_all.py --predictions_dir outputs/mixtral_512 --scores_dir scores_recomputed/mixtral_512 --sari_method standard
```

Important options:

- `--sari_method legacy`: uses the previous project implementation.
- `--sari_method standard`: uses `evaluate.load("sari")`.
- `--sari_method auto`: tries standard SARI and falls back to legacy if needed.
- `--eval_semantic True`: computes BERTScore-F1 and MeaningBERT.
- `--overwrite True`: recomputes existing score files.

The aggregate file is saved as:

```text
<scores_dir>/all_scores.csv
```

## Adding Per-Example Metrics

`add_prediction_metrics.py` adds per-example columns to the prediction CSV files in `outputs/`: lengths, sentence-level BLEU, SARI, FKGL, FRE, BERTScore-F1, and MeaningBERT.

```powershell
python add_prediction_metrics.py --outputs_dir outputs --sari_method standard --force True
```

This command modifies prediction CSVs in place. Use a working copy if the
metrics are already present in the final artifacts. Sentence-level BLEU is not
the corpus BLEU reported in tables.

## Error Analysis

`extract_low_sari_records.py` selects the examples with the lowest SARI scores from each prediction file and generates JSON files in `error_analysis/`.

```powershell
python extract_low_sari_records.py --input outputs --output_dir error_analysis --metric SARI --top_n 15
```

The command above creates a separate extraction directory; it does not recreate
all the curated evidence reports. The final report entry points are:

- [Selected configurations](error_analysis_candidates_512/error_analysis_experiment_selection.html)
- [All reports](error_analysis_candidates_512/all_error_analysis_reports.html)
- [High-performing evidence](error_analysis_candidates_512/high_performing_error_evidence.html)
- [Lower-performing evidence](error_analysis_candidates_512/lower_performing_error_evidence.html)
- [Comparative evidence](error_analysis_candidates_512/comparative_error_evidence.html)

Download the repository and open the HTML files locally to view them. They use
relative links to individual evidence examples.

The final HTML reports are provided for inspection. Their presentation-generation
scripts are not included; the example-selection script is provided above.

The qualitative reports examine selected low-SARI examples and should not be
interpreted as estimates of error prevalence across all generated outputs.

## Data

See `data/README.md` for expected columns and TSAR reference files, and
the dataset licensing notes in that file for source information and uncertainties.
Source and reference texts also occur in prediction files,
HTML reports, and prompt demonstrations; their inclusion does not grant new
rights to redistribute the underlying datasets. No new dataset license is
implied by this repository.

PLABA's license has been indicated as CC BY, without a confirmed version.
See `data/README.md` for details; the code license does not apply
to the dataset.

## Code License

The project's original code is distributed under the [MIT License](LICENSE).
Copyright (c) 2026 Isabel Segura-Bedmar, Alberto Díaz, Rémi Cardon.

This license does not apply to datasets or third-party texts reproduced in
prompts, prediction files, or reports. Third-party code and dependencies retain
their respective licenses. See `data/README.md` for dataset information.

## Python Scripts

- `main.py`: runs inference and generates predictions.
- `run_all_dataset.py`: launches multiple `main.py` configurations in batch; edit the internal configuration before running it.
- `evaluate_all.py`: computes aggregate metrics for all prediction files.
- `add_prediction_metrics.py`: adds per-example metrics to prediction CSV files.
- `extract_low_sari_records.py`: extracts the worst cases according to SARI for qualitative analysis.
- `data_utils.py`: loads datasets and prompts, and manages prediction output paths.
- `model_utils.py`: loads models and runs simplification with either the `hf` or `ollama` backend.
- `eval_utils.py`: implements the evaluation metrics.
- `logger_utils.py`: creates logs and records runtime/GPU information.

## Conventions

- Prompt types: `minimal`, `iso`, `iso_examples`.
- Strategies: `zero`, `one`, `few`.
- Few-shot sampling methods: `random`, `metric`.
- Flesch Reading Ease is named `FRE`.
- Final paper scores use standard SARI; do not mix them with historical legacy evaluations.

## Citation

If you use this repository or reference our work, please cite our submitted manuscript:

> **ISO-Based and Minimal Prompting for Text Simplification: An Empirical Evaluation with Large Language Models**  
> Isabel Segura-Bedmar, Alberto Díaz, and Rémi Cardon  
> *Submitted to IEEE Access*, 2026.

```bibtex
@unpublished{segurabedmar2026isobased,
  title  = {ISO-Based and Minimal Prompting for Text Simplification: An Empirical Evaluation with Large Language Models},
  author = {Segura-Bedmar, Isabel and D{\'i}az, Alberto and Cardon, R{\'e}mi},
  note   = {Submitted to IEEE Access},
  year   = {2026}
}
```
