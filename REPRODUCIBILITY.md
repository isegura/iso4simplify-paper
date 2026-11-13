# Reproducibility

## Recorded settings

Both local instruction-tuned models use an 8,192-token context and a 512-token generation limit. Recorded decoding settings are temperature 0, top-k 1, top-p 1.0, generation seed 42, repetition penalty 1.1 and repeat-last-n 64. The dedicated penalty diagnostic changes repetition penalty to 1.0. Demonstration-selection seeds and the diagnostic-subset sampling seed are separate from generation seed.

Model identifiers are `llama3.1:8b` and `mixtral:latest`; quantization formats reported for the study are Q4_K_M and Q4_0, respectively. Model tags are mutable. Saved provenance and metadata should be consulted when reproducing a particular run; fixed decoding parameters alone do not ensure identical outputs across environments.

Recorded Ollama versions differ between experiment groups: v0.23.1 for the initial environment, v0.40.6 for the ablation and v0.40.13 for retrieval. These environment records must not be interpreted as independent per-output attestations for every historical run. Consult preserved environment/manifests for the relevant experiment. The release does not assert that every run used one common Ollama version.

## Inspect and rebuild reports without inference

Open `experiments/html_reports_20261113/reports/index.html` locally. To rebuild those HTML files from saved predictions and scores:

```powershell
python experiments/html_reports_20261113/build_reports.py
```

The builder never runs inference or recomputes metrics. Its manifest and verification file record coverage and source hashes. Source paths are retained from the working analysis tree.

Other descriptive and statistical scripts are provided alongside their frozen inputs and results. The current main statistical entry point is `experiments/joint_analysis_all_pairs/run_analysis.py`; it depends on `joint_analysis_final` and the shared statistics code in `reviewer2_concern2`. Read each program's arguments before execution: `--execute` may run an analysis or, for generation programs, model inference. No command has been run merely by assembling this release candidate. Full end-to-end reproduction has not been tested in a clean environment.

## Inference entry points

- Original conditions: root `main.py` and saved `prompts/`.
- Additional random selections: `experiments/reviewer2_concern2/study.py`, manifests and frozen demonstrations.
- Retrieval: `experiments/reviewer2_concern5/prepared_study.py` and `prepared_retrieval_20261102/`.
- Ablation: root `run_focused_ablation.py` and the saved ablation prompts/manifests.
- Penalty diagnostic: `experiments/reviewer2_concern4/repeat_penalty/cochrane_iso_shared_subset/study.py`.

Use a separate output directory when reproducing generation. Some historical scripts contain workstation-specific paths and completion checks; inspect these before execution. Released results can be inspected independently of inference. Do not mix legacy SARI variants or earlier scalar-contrast families with the current all-pairs results.
