import ctypes
import platform
import re
import subprocess
import sys
from pathlib import Path


print(f"Ejecutando en plataforma: {platform.system()} {platform.release()}")

PYTHON = sys.executable

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

if sys.platform == "win32":
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

MODEL = "llama3.1:8b"
BACKEND = "ollama"
DATASET = "cochrane"
PROMPTS = ["minimal", "iso", "iso_examples"]
STRATEGIES = ["zero", "one", "few"]
SAMPLING_METHODS = ["random", "metric"]

HEAD = None
MAX_NEW_TOKENS = "256"
OUTPUTS_DIR = Path("outputs_256")

OLLAMA_NUM_CTX = "8192"
OLLAMA_TEMPERATURE = "0"
OLLAMA_SEED = "42"
OLLAMA_TOP_K = "1"
OLLAMA_TOP_P = "1.0"
OLLAMA_REPEAT_PENALTY = "1.1"
OLLAMA_REPEAT_LAST_N = "64"
OLLAMA_NUM_GPU = "999"
OLLAMA_TIMEOUT = "900"


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


try:
    print(f"Python usado: {PYTHON}")
    print(
        "Diagnostic rerun: "
        f"model={MODEL}, dataset={DATASET}, max_new_tokens={MAX_NEW_TOKENS}"
    )

    for prompt_type in PROMPTS:
        for strategy in STRATEGIES:
            if strategy == "few":
                sampling_values = SAMPLING_METHODS
            else:
                sampling_values = [None]

            for sampling_method in sampling_values:
                cmd = [
                    PYTHON, "main.py",
                    "--backend", BACKEND,
                    "--model", MODEL,
                    "--type_prompt", prompt_type,
                    "--strategy", strategy,
                    "--dataset", DATASET,
                    "--outputs_dir", str(OUTPUTS_DIR),
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

                if sampling_method is not None:
                    cmd.extend(["--sampling_method", sampling_method])
                if HEAD is not None:
                    cmd.extend(["--head", HEAD])

                out_path = expected_output_path(
                    MODEL, DATASET, prompt_type, strategy, sampling_method
                )
                run_if_missing(cmd, out_path)
finally:
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
