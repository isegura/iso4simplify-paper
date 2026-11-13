"""Evaluate the six Mixtral ablations and nine original Mixtral zero-shot comparators.

Original prediction files and eval_utils.py are never modified.
Checkpoints are keyed by prediction/source/reference and evaluator hashes.
"""
import hashlib
import json
import os
from pathlib import Path
import time
import importlib.metadata

from focused_metric_runtime import configure, MODULE
configure()

import pandas as pd
import numpy as np
from eval_utils import evaluate_predictions
from evaluate_all import load_data_tsar
from run_focused_ablation import prepare, EXPECTED, rows, aligned

ROOT = Path(__file__).resolve().parent
SHARED = ROOT / "experiments" / "focused_ablation"
BASE = SHARED / "mixtral"
DEST = BASE / "evaluation"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.chdir(ROOT)
    validation = json.loads((SHARED / "meaningbert_validation/verification.json").read_text(encoding="utf-8"))
    if not validation["all_match"] or validation["meaningbert_module_sha256"] != digest(MODULE):
        raise ValueError("MeaningBERT historical score validation has not passed")
    DEST.mkdir(exist_ok=True)
    for dataset in EXPECTED:
        for prompt in ("iso", "iso_examples"):
            data, source, prompt_path, path, _ = prepare(dataset, prompt, "mixtral:latest")
            record = json.loads((BASE / "logs" / f"{dataset}_{prompt}_ablated_zero.json").read_text())
            assert record["status"] == "complete" and record["returncode"] == 0
            generated = rows(path)
            aligned(generated, data)
            assert record["processed"] == len(generated) == EXPECTED[dataset]
            assert record["source_sha256"] == digest(source)
            assert record["prompt_sha256"] == digest(prompt_path)
            assert all(r["prediction"].strip() and r.get("done_reason") for r in generated)
    versions = {name: importlib.metadata.version(name) for name in
                ("evaluate", "sacrebleu", "bert-score", "textstat", "transformers", "torch", "numpy")}
    (DEST / "methodology.json").write_text(json.dumps({
        "model": "mixtral:latest", "versions": versions, "sari": "standard; evaluate.load('sari'); no legacy fallback",
        "original_metrics": "eval_utils.evaluate_predictions, English, eval_semantic=True; unchanged",
        "meaningbert_reference": "source", "tsar_references": "A2/B1 jointly via load_data_tsar",
        "meaningbert_module_sha256": digest(MODULE),
        "word_count": "len(text.split())", "compression": "mean of output/source whitespace word count ratios",
        "copy_rate": "mean fraction of output whitespace tokens occurring exactly in source token set; case-sensitive, punctuation retained; empty output=0",
        "truncation": "all outputs retained, including done_reason=length",
        "copy_rate_scale": "0 to 1; lexical overlap, not phrase-copy measurement"
    }, indent=2), encoding="utf-8")
    combined = []
    discrepancies = []
    for dataset in EXPECTED:
        for prompt in ("iso_ablated", "iso_examples_ablated", "minimal", "iso", "iso_examples"):
            ablated = prompt.endswith("_ablated")
            folder = BASE / "predictions" / "mixtral" if ablated else ROOT / "outputs" / "mixtral_512"
            path = folder / f"predictions_mixtral_latest_{dataset}_{prompt}_zero.csv"
            checkpoint = DEST / f"{dataset}_{prompt}.json"
            fingerprint = {"prediction": digest(path), "evaluator": digest(ROOT / "eval_utils.py"),
                           "meaningbert_module": digest(MODULE),
                           "metric_runtime": digest(ROOT / "focused_metric_runtime.py"),
                           "meaningbert_provenance": digest(SHARED / "metric_sources/provenance.json"),
                           "loader": digest(ROOT / "evaluate_all.py"), "driver": digest(Path(__file__)),
                           "versions": versions}
            if dataset == "tsar2025":
                fingerprint["gold"] = digest(ROOT / "data/tsar2025/tsar2025_test_200.csv")
            print(f"START {dataset} {prompt}", flush=True)
            if checkpoint.exists():
                saved = json.loads(checkpoint.read_text(encoding="utf-8"))
                assert saved["fingerprint"] == fingerprint, "Checkpoint inputs changed"
                record = saved["record"]
            else:
                df = pd.read_csv(path, keep_default_na=False)
                aligned(rows(path), rows(ROOT / "data" / dataset / f"{dataset}_test.csv"))
                if dataset == "tsar2025":
                    predictions, sources, references, refs_bleu, joined = load_data_tsar(
                        path, ROOT / "data/tsar2025/tsar2025_test_200.csv")
                    assert joined["text_id"].astype(str).tolist() == df["text_id"].astype(str).tolist()
                    assert sources == df["original"].astype(str).tolist()
                    assert all(len(refs) == 2 for refs in references)
                else:
                    predictions = df["prediction"].astype(str).tolist()
                    sources = df["original"].astype(str).tolist()
                    references = df["reference"].astype(str).tolist()
                    refs_bleu = None
                assert len(predictions) == EXPECTED[dataset] and all(p.strip() for p in predictions)
                start = time.perf_counter()
                scores = evaluate_predictions(predictions, sources, references, refs_bleu,
                                              lang="en", eval_semantic=True, sari_method="standard")
                word_lengths = [len(p.split()) for p in predictions]
                source_lengths = [len(s.split()) for s in sources]
                assert all(source_lengths), "Zero-length source: compression undefined"
                compression = [p / s for p, s in zip(word_lengths, source_lengths)]
                copies = [sum(t in set(s.split()) for t in p.split()) / len(p.split()) if p.split() else 0
                          for p, s in zip(predictions, sources)]
                scores.update(output_length=float(np.mean(word_lengths)),
                              compression_ratio=float(np.mean(compression)), copy_rate=float(np.mean(copies)))
                assert all(np.isfinite(float(value)) for value in scores.values())
                record = {"dataset": dataset, "prompt": prompt, "n": len(predictions), **scores}
                items = pd.DataFrame({"row_index": range(len(df)), "text_id": df["text_id"],
                    "output_length": word_lengths, "source_length": source_lengths,
                    "compression_ratio": compression, "copy_rate": copies})
                items.to_csv(DEST / f"{dataset}_{prompt}_descriptive_items.csv", index=False)
                checkpoint.write_text(json.dumps({"fingerprint": fingerprint, "record": record,
                    "elapsed_seconds": time.perf_counter() - start}, indent=2), encoding="utf-8")
            combined.append(record)
            pd.DataFrame(combined).to_csv(DEST / "all_metrics.csv", index=False)
            pd.DataFrame([r for r in combined if r["prompt"].endswith("_ablated")]).to_csv(
                DEST / "ablation_metrics.csv", index=False)
            if not ablated:
                old = pd.read_csv(ROOT / "scores_512/mixtral_512" / f"scores_mixtral_latest_{dataset}_{prompt}_zero.csv").iloc[0]
                for metric in ("SARI", "BLEU", "BERTScore-F1", "MeaningBERT", "FKGL", "FRE"):
                    discrepancies.append({"dataset": dataset, "prompt": prompt, "metric": metric,
                        "saved": float(old[metric]), "recomputed": record[metric],
                        "delta": float(record[metric]) - float(old[metric])})
            print(f"DONE {record}", flush=True)
    pd.DataFrame(discrepancies).to_csv(DEST / "original_score_check.csv", index=False)
    (DEST / "complete.json").write_text(json.dumps({"status": "complete", "configurations": len(combined),
        "ablations": 6, "original_comparators": 9}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
