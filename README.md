# iso4simplify

Code, prompts, saved predictions and analyses for the manuscript **ISO-Based and Baseline Prompting for Text Simplification: An Empirical Evaluation with Two Instruction-Tuned Language Models**, submitted to IEEE Access.

## Current study

The main study contains **162 configurations and 20,142 generated outputs** across Cochrane, PLABA and TSAR 2025, two models and three prompt types: Baseline (`minimal` in filenames), ISO and ISO+examples. Five strategies are evaluated: zero-shot, one-shot, random few-shot, fixed metric-based few-shot and per-input retrieval-based few-shot. One-shot and random few-shot use demonstration-selection seeds 42, 44 and 46. The other strategies enter once per dataset/model/prompt combination. Each few-shot prompt uses three demonstrations.

The primary inferential metric is SARI. The joint analysis reports 14 global contrasts, 78 model–dataset contrasts and 15 Wald tests. Other metrics and output descriptors are reported descriptively. Random-condition tables report the mean and sample standard deviation across three fixed selections; these do not quantify uncertainty over arbitrary demonstration sets.

Separate experiments contain 1,492 newly generated zero-shot ablation outputs (12 configurations) and a repetition-penalty diagnostic of 62 outputs on 31 selected Cochrane texts. Neither is included in the main-study totals.

## Start here

- [Results and artifact map](RESULTS_GUIDE.md).
- [Reproduction and inference settings](REPRODUCIBILITY.md).
- [Complete HTML report index](experiments/html_reports_20261113/reports/index.html). Download or clone the repository and open this file locally; GitHub displays HTML source rather than rendering the reports.
- [Main-study configuration manifest](experiments/html_reports_20261113/manifest.json).
- [Release status](RELEASE_STATUS.md).

Saved predictions and item-level scores are the inputs for the released analyses. No human evaluation or quantitative assessment of adherence to individual ISO principles is claimed. Automatic screening indicators are candidates, not confirmed error rates. Historical qualitative selections remain distinct from the new full-coverage reports.

## Layout

`data/` holds evaluation splits and dataset attribution; `prompts/` holds the original fixed templates. `outputs/*_512/` contains the original 72 main-study runs. The additional 72 seed runs and 18 retrieval runs retain their original paths under `experiments/` so that source hashes and analysis manifests remain usable. `scores_512/` contains historical aggregates; **it is not the complete current results table**. Use the artifact map for the current results.

Folders named `reviewer2_concern*` are archival implementation paths retained for reproducibility. Current scientific conclusions use the all-pairs joint analysis, not older intermediate statistical plans.

## Installation

Create a Python environment and install `requirements_windows.txt`; install Ollama separately for inference. Individual evaluation programs may require additional packages or pretrained metric downloads. Saved CSVs and HTML reports can be inspected without running models. See REPRODUCIBILITY.md before executing any generation or evaluation command.

## Licensing and citation

Original project code is distributed under the [MIT license](LICENSE). Dataset and third-party-text terms are separate: see [data attribution and licenses](data/README.md), including for texts reproduced in predictions and HTML reports. Citation metadata for the software and manuscript is in CITATION.cff. The expanded study is available on the main branch; the older v1.0.3 tag identifies the earlier artifact set.

## Manuscript citation

```bibtex
@unpublished{segurabedmar2026isobased,
  title = {ISO-Based and Baseline Prompting for Text Simplification: An Empirical Evaluation with Two Instruction-Tuned Language Models},
  author = {Segura-Bedmar, Isabel and D{\'i}az, Alberto and Cardon, R{\'e}mi},
  note = {Submitted to IEEE Access},
  year = {2026}
}
```
