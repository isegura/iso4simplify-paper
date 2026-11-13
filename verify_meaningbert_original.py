"""Validate MeaningBERT only on the nine saved original zero-shot configurations."""
import json
from pathlib import Path
import time
from focused_metric_runtime import configure, BASE, ROOT, MODULE

configure()
import pandas as pd
from eval_utils import compute_meaningbert
from evaluate_all import load_data_tsar
from run_focused_ablation import EXPECTED, rows, aligned
from hashlib import sha256


def main():
    destination = BASE / "meaningbert_validation"
    destination.mkdir(exist_ok=True)
    results = []
    for dataset, n in EXPECTED.items():
        for prompt in ("minimal", "iso", "iso_examples"):
            path = ROOT / "outputs/llama_512" / f"predictions_llama3_1_8b_{dataset}_{prompt}_zero.csv"
            aligned(rows(path), rows(ROOT / "data" / dataset / f"{dataset}_test.csv"))
            old_path = ROOT / "scores_512/llama_512" / f"scores_llama3_1_8b_{dataset}_{prompt}_zero.csv"
            old = float(pd.read_csv(old_path).iloc[0]["MeaningBERT"])
            if dataset == "tsar2025":
                predictions, sources, _, _, joined = load_data_tsar(path, ROOT / "data/tsar2025/tsar2025_test_200.csv")
                assert len(joined) == n
            else:
                df = pd.read_csv(path, keep_default_na=False)
                predictions, sources = df.prediction.astype(str).tolist(), df.original.astype(str).tolist()
            print(f"START {dataset} {prompt}: {n} items; saved={old}", flush=True)
            start = time.perf_counter()
            score = compute_meaningbert(predictions, sources)
            record = {"dataset": dataset, "prompt": prompt, "n": n, "saved": old,
                      "recomputed": score, "delta": round(score-old, 8),
                      "exact_at_reported_precision": score == old,
                      "elapsed_seconds": time.perf_counter()-start,
                      "prediction_sha256": sha256(path.read_bytes()).hexdigest()}
            results.append(record)
            pd.DataFrame(results).to_csv(destination / "original_scores.csv", index=False)
            print(f"DONE {record}", flush=True)
    report = {"all_match": all(r["exact_at_reported_precision"] for r in results),
              "meaningbert_module_sha256": sha256(MODULE.read_bytes()).hexdigest(),
              "comparisons": results, "reference": "source", "device": "CPU, unchanged original module"}
    (destination / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"ALL MATCH: {report['all_match']}", flush=True)


if __name__ == "__main__":
    main()
