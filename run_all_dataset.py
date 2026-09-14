import subprocess
import sys
from pathlib import Path
import re

import platform
import ctypes

print(f"Ejecutando en plataforma: {platform.system()} {platform.release()}")

PYTHON = sys.executable

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


# Esto solo funciona en Windows
if sys.platform == "win32":
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

# Configuracion
models = ["llama3.1:8b", "mixtral:latest"]
BACKEND = "ollama"

#datasets_es = ["CIMA", "EdudraCT", "NCI"]
datasets = ["cochrane", "plaba", "tsar2025"]  # datasets en ingles

prompts = ["minimal", "iso", "iso_examples"]
strategies = ["zero", "one", "few"]

sampling_methods = ["random", "metric"]
HEAD = None
MAX_NEW_TOKENS = "512"
OLLAMA_NUM_CTX = "8192"
OLLAMA_TEMPERATURE = "0"
OLLAMA_SEED = "42"
OLLAMA_TOP_K = "1"
OLLAMA_TOP_P = "1.0"
OLLAMA_REPEAT_PENALTY = "1.1"
OLLAMA_REPEAT_LAST_N = "64"
OLLAMA_NUM_GPU = "999"
OLLAMA_TIMEOUT = "900"
OUTPUTS_DIR = Path("reruns")

print(f"Python usado: {PYTHON}")
def run_command(cmd):
    print("\n" + "=" * 80)
    print("Ejecutando:")
    print(" ".join(cmd))
    print("=" * 80 + "\n")

    subprocess.run(cmd, check=True)

def expected_output_path(model_name, dataset, prompt_type, strategy, sampling_method=None):
    model_short = model_name.split("/")[-1]
    model_short = re.sub(r"[:.]+", "_", model_short)
    model_family = model_short.lower().split("_")[0]
    if model_family.startswith("llama"):
        model_family = "llama"

    if strategy == "few":
        filename = f"predictions_{model_short}_{dataset}_{prompt_type}_{strategy}_{sampling_method}.csv"
    else:
        filename = f"predictions_{model_short}_{dataset}_{prompt_type}_{strategy}.csv"

    return OUTPUTS_DIR / model_family / filename

def run_if_missing(cmd, out_path):
    if out_path.exists():
        print(f"Saltando configuracion, ya existe: {out_path}")
        return
    run_command(cmd)

for model in models:
    for dataset in datasets:
        print(
            f"Ejecutando evaluaciones para el dataset '{dataset}' "
            f"con el modelo '{model}' usando el backend '{BACKEND}'."
            )
        for p in prompts:
            for s in strategies:
                if s == "few":
                    for sm in sampling_methods:
                        cmd = [
                                PYTHON, "main.py",
                                "--backend", BACKEND,
                                "--outputs_dir", str(OUTPUTS_DIR),
                                "--model", model,
                                "--type_prompt", p,
                                "--strategy", s,
                                "--sampling_method", sm,
                                "--dataset", dataset,
                                "--max_new_tokens", MAX_NEW_TOKENS,
                                "--ollama_num_ctx", OLLAMA_NUM_CTX,
                                "--ollama_temperature", OLLAMA_TEMPERATURE,
                                "--ollama_seed", OLLAMA_SEED,
                                "--ollama_top_k", OLLAMA_TOP_K,
                                "--ollama_top_p", OLLAMA_TOP_P,
                                "--ollama_repeat_penalty", OLLAMA_REPEAT_PENALTY,
                                "--ollama_repeat_last_n", OLLAMA_REPEAT_LAST_N,
                                "--ollama_num_gpu", OLLAMA_NUM_GPU,
                                "--ollama_require_gpu",
                                "--ollama_timeout", OLLAMA_TIMEOUT,
                            ]
                        if HEAD is not None:
                            cmd.extend(["--head", HEAD])
                        out_path = expected_output_path(model, dataset, p, s, sm)
                        run_if_missing(cmd, out_path)
                else:
                    cmd = [
                                PYTHON, "main.py",
                                "--backend", BACKEND,
                                "--outputs_dir", str(OUTPUTS_DIR),
                                "--model", model,
                                "--type_prompt", p,
                                "--strategy", s,
                                "--dataset", dataset,
                                "--max_new_tokens", MAX_NEW_TOKENS,
                                "--ollama_num_ctx", OLLAMA_NUM_CTX,
                                "--ollama_temperature", OLLAMA_TEMPERATURE,
                                "--ollama_seed", OLLAMA_SEED,
                                "--ollama_top_k", OLLAMA_TOP_K,
                                "--ollama_top_p", OLLAMA_TOP_P,
                                "--ollama_repeat_penalty", OLLAMA_REPEAT_PENALTY,
                                "--ollama_repeat_last_n", OLLAMA_REPEAT_LAST_N,
                                "--ollama_num_gpu", OLLAMA_NUM_GPU,
                                "--ollama_require_gpu",
                                "--ollama_timeout", OLLAMA_TIMEOUT,
                            ]
                    if HEAD is not None:
                        cmd.extend(["--head", HEAD])
                    print(f"Ejecutando comando: {' '.join(cmd)}")
                    out_path = expected_output_path(model, dataset, p, s)
                    run_if_missing(cmd, out_path)

# Restaurar comportamiento normal

if sys.platform == "win32":
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
