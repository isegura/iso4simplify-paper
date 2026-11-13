"""Focused ablation: dry-run by default; --execute requires prior human approval.

Uses main.py unchanged apart from the two new zero-shot prompt mappings.
Never resumes or overwrites an existing prediction or execution record.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
EXPECTED = {"cochrane": 125, "plaba": 148, "tsar2025": 100}
RUNS = ROOT / "experiments" / "focused_ablation"
MODELS = {
    "llama3.1:8b": ("llama_512", "llama3_1_8b", "llama"),
    "mixtral:latest": ("mixtral_512", "mixtral_latest", "mixtral"),
}


def run_directory(model):
    return RUNS if model == "llama3.1:8b" else RUNS / "mixtral"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def aligned(actual, expected):
    if len(actual) != len(expected):
        raise ValueError(f"Incomplete/misaligned file: {len(actual)} != {len(expected)}")
    for index, (left, right) in enumerate(zip(actual, expected)):
        for field in ("text_id", "original", "reference"):
            if left[field] != right[field]:
                raise ValueError(f"Alignment mismatch at row {index}, {field}")


def prepare(dataset, prompt, model="llama3.1:8b"):
    original_folder, model_short, family = MODELS[model]
    runs = run_directory(model)
    source = ROOT / "data" / dataset / f"{dataset}_test.csv"
    data = rows(source)
    if len(data) != EXPECTED[dataset]:
        raise ValueError(f"Unexpected test size: {source}")
    for original_prompt in ("minimal", "iso", "iso_examples"):
        original = ROOT / "outputs" / original_folder / f"predictions_{model_short}_{dataset}_{original_prompt}_zero.csv"
        aligned(rows(original), data)
    original_path = ROOT / "prompts" / f"{prompt}_zero.md"
    ablated_path = ROOT / "prompts" / f"{prompt}_zero_ablated.md"
    original = original_path.read_bytes()
    start = original.index(b"# PRINCIPLES OF ORGANIZATION AND HIERARCHY")
    end = original.index(b"# WRITING INSTRUCTIONS (LINGUISTIC LEVEL)", start)
    if ablated_path.read_bytes() != original[:start] + original[end:]:
        raise ValueError("Ablated prompt differs outside the designated section")
    label = f"{prompt}_ablated"
    output = runs / "predictions" / family / f"predictions_{model_short}_{dataset}_{label}_zero.csv"
    command = [sys.executable, str(ROOT / "main.py"),
               "--backend", "ollama", "--model", model,
               "--dataset", dataset, "--type_prompt", label, "--strategy", "zero",
               "--outputs_dir", str(runs / "predictions"),
               "--max_new_tokens", "512", "--ollama_num_ctx", "8192",
               "--ollama_temperature", "0.0", "--ollama_seed", "42",
               "--ollama_top_k", "1", "--ollama_top_p", "1.0",
               "--ollama_repeat_penalty", "1.1", "--ollama_repeat_last_n", "64",
               "--ollama_num_gpu", "999", "--ollama_require_gpu", "--ollama_timeout", "900"]
    return data, source, ablated_path, output, command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=EXPECTED, required=True)
    parser.add_argument("--prompt", choices=("iso", "iso_examples"), required=True)
    parser.add_argument("--model", choices=MODELS, default="llama3.1:8b")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    runs = run_directory(args.model)
    data, source, prompt, output, command = prepare(args.dataset, args.prompt, args.model)
    print(subprocess.list2cmdline(command), flush=True)
    print(f"Verified {len(data)} aligned inputs; prompt differs only by the specified deletion.", flush=True)
    if not args.execute:
        print("DRY RUN: no generation or evaluation performed.")
        return
    records = runs / "logs"
    records.mkdir(parents=True, exist_ok=True)
    stem = f"{args.dataset}_{args.prompt}_ablated_zero"
    manifest_path = records / f"{stem}.json"
    console_path = records / f"{stem}.log"
    if any(path.exists() for path in (output, manifest_path, console_path)):
        raise FileExistsError("Existing ablation artifacts: refusing to overwrite or resume")
    # Read-only API: record exact installed digest/quantization, never pull a model.
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=10) as response:
        tags = json.load(response)
    model = next(m for m in tags["models"] if m["name"] == args.model)
    with urllib.request.urlopen("http://localhost:11434/api/version", timeout=10) as response:
        version = json.load(response)
    provenance = runs / "model_provenance.json"
    identity = {"digest": model["digest"], "details": model.get("details"), "ollama_version": version}
    inspection = json.loads((runs / "inspection.json").read_text(encoding="utf-8"))
    inspected = inspection["installed_model"][0]
    if model["digest"] != inspected["digest"] or version != inspection["ollama_version"]:
        raise ValueError("Model/runtime changed since preparation; inform the user before proceeding")
    if provenance.exists():
        if json.loads(provenance.read_text(encoding="utf-8")) != identity:
            raise ValueError("Model/runtime changed between ablation runs; stopping")
    else:
        with provenance.open("x", encoding="utf-8") as handle:
            json.dump(identity, handle, indent=2)
    manifest = {"status": "running", "command": command, "expected": len(data),
                "model": model, "ollama_version": version,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest()}
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    start = time.perf_counter()
    try:
        with console_path.open("x", encoding="utf-8") as console:
            result = subprocess.run(command, cwd=ROOT, stdout=console, stderr=subprocess.STDOUT)
        manifest["returncode"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"Inference failed: see {console_path}")
        generated = rows(output)
        aligned(generated, data)
        if any(not row["prediction"].strip() or not row.get("done_reason") for row in generated):
            raise ValueError("Empty output or missing termination metadata; inspect before evaluation")
        manifest.update(status="complete", processed=len(generated),
                        truncated=sum(r["done_reason"] == "length" for r in generated))
    except BaseException as exc:
        manifest.update(status="incomplete", error=str(exc))
        raise
    finally:
        manifest["elapsed_seconds"] = time.perf_counter() - start
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
