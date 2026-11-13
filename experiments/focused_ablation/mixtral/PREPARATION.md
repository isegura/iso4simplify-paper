# Mixtral extension — prepared, not executed

Repeat the same focused organization/summary ablation for the second model
already used in the paper: Mixtral 8x7B via `mixtral:latest`.

## Six configurations

ISO ablated and ISO+examples ablated, zero-shot, on Cochrane (125 rows),
PLABA (148), TSAR2025 (100). Total: 746 new predictions. The two prompt files
are reused without any edit; see ../iso.diff and ../iso_examples.diff.
Sources, references and input order match all nine original Mixtral zero-shot
prediction files. PLABA repeated IDs remain unchanged and are matched by row,
source and reference as well as ID.

## Parameters checked against all six original matched logs

Ollama `mixtral:latest`, output limit 512, context 8192, temperature 0,
seed 42, top_k 1, top_p 1.0, repeat_penalty 1.1, repeat_last_n 64,
num_gpu 999, GPU required, timeout 900 seconds. No preprocessing/postprocessing
or inference function changes. GPU required means the existing pipeline's
GPU-use check; it does not certify that every layer fits in VRAM.

Installed model: Q4_0, digest
a3b6bef0f836ff29ddb576a80eeb1b7def43ec9b809466f62e96adb871fe8498.
Ollama version at preparation: 0.40.6. Installed model metadata reports 46.7B
total parameters, consistent with the existing Mixtral model; no new model is
downloaded or substituted. Historical digest/runtime identity is not certified
by the older run logs. Detailed evidence and all six expanded main.py commands
are in inspection.json. The launcher stops if model/runtime changes after this
inspection or between runs.

## Implementation and isolation

run_focused_ablation.py now accepts `--model mixtral:latest`.
Its default remains Llama; all six default Llama command lists were compared
against their original inspection and are identical. The shared main.py and
prompt contents are unchanged by this extension.

Mixtral outputs and provenance use this separate directory:

- `predictions/mixtral/predictions_mixtral_latest_<dataset>_<prompt>_ablated_zero.csv`
- `logs/<dataset>_<prompt>_ablated_zero.log` and corresponding completion JSON
- `model_provenance.json` (created only on execution)

The main inference script also creates its usual timestamped detailed logs
under the root logs/ directory. Captured logs here include stdout/stderr.
The launcher refuses existing outputs/run records and does not resume partial
runs. It checks exact expected counts, alignment, nonempty outputs, termination
metadata and exit codes, and records elapsed time and truncation counts.

No original prediction, Llama result, score, tag or commit is overwritten.

## Manual launch

Keep Ollama running. From the project root:

```powershell
.\experiments\focused_ablation\mixtral\commands.ps1
```

The script invokes the existing .venv interpreter directly; activation is not
required. It runs the six commands sequentially and stops on any failure.
This file is prepared only; no inference was launched during preparation.

To inspect the first run from another PowerShell window:

```powershell
Get-Content .\experiments\focused_ablation\mixtral\logs\cochrane_iso_ablated_zero.log -Tail 20 -Wait
```

For a dry run only (no generation):

```powershell
.\.venv\Scripts\python.exe .\run_focused_ablation.py --model mixtral:latest --dataset cochrane --prompt iso
```

After the six executions, verify completeness, alignment and truncation before
evaluation. The earlier `../evaluate.ps1` targets the completed Llama study;
do not use it to evaluate these new Mixtral files. Mixtral evaluation and the
combined two-model report will be prepared after successful inference.
