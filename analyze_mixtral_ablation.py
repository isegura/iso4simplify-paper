"""Paired SARI bootstrap and randomization tests; no inference/semantic models."""
from focused_metric_runtime import configure, BASE, ROOT
configure()
BASE = BASE / "mixtral"
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from eval_utils import get_sari_metric
from evaluate_all import load_data_tsar
from run_focused_ablation import EXPECTED, rows, aligned

BOOTSTRAPS = 10000
PERMUTATIONS = 19999
SEED = 42


def main():
    started = time.perf_counter()
    destination = BASE / "statistics"
    destination.mkdir(exist_ok=True)
    assert json.loads((BASE / "evaluation/complete.json").read_text())["configurations"] == 15
    scores = pd.read_csv(BASE / "evaluation/all_metrics.csv")
    metric = get_sari_metric()
    module = importlib.import_module(metric.__class__.__module__)
    # The inspected corpus implementation calls normalize and SARIsent per row,
    # then divides their sum by n. Cache only these deterministic inner operations.
    # Every bootstrap/permutation still executes that corpus implementation twice.
    original_kernel = module.SARIsent
    @lru_cache(maxsize=None)
    def cached_kernel(source, prediction, refs):
        return original_kernel(source, prediction, refs)
    module.normalize = lru_cache(maxsize=None)(module.normalize)
    module.SARIsent = lambda source, prediction, refs: cached_kernel(source, prediction, tuple(refs))

    def corpus(sources, predictions, references):
        return float(metric._compute(sources=sources, predictions=predictions, references=references)["sari"])

    comparisons = []
    seeds = np.random.SeedSequence(SEED).spawn(12)
    for config_index, (dataset, prompt) in enumerate((d,p) for d in EXPECTED for p in ("iso", "iso_examples")):
        n = EXPECTED[dataset]
        original_path = ROOT / "outputs/mixtral_512" / f"predictions_mixtral_latest_{dataset}_{prompt}_zero.csv"
        ablated_path = BASE / "predictions/mixtral" / f"predictions_mixtral_latest_{dataset}_{prompt}_ablated_zero.csv"
        original_rows, ablated_rows = rows(original_path), rows(ablated_path)
        aligned(ablated_rows, original_rows)
        aligned(original_rows, rows(ROOT / "data" / dataset / f"{dataset}_test.csv"))
        if dataset == "tsar2025":
            original, sources, references, _, joined = load_data_tsar(original_path, ROOT / "data/tsar2025/tsar2025_test_200.csv")
            ablated, sources_b, references_b, _, joined_b = load_data_tsar(ablated_path, ROOT / "data/tsar2025/tsar2025_test_200.csv")
            assert sources == sources_b and references == references_b
            assert joined.text_id.tolist() == joined_b.text_id.tolist()
        else:
            sources = [r["original"] for r in original_rows]
            original = [r["prediction"] for r in original_rows]
            ablated = [r["prediction"] for r in ablated_rows]
            references = [[r["reference"]] for r in original_rows]
        assert len(sources) == len(original) == len(ablated) == len(references) == n
        # Validate optimized execution against the unchanged public metric API.
        full_o = float(metric.compute(sources=sources, predictions=original, references=references)["sari"])
        full_a = float(metric.compute(sources=sources, predictions=ablated, references=references)["sari"])
        assert corpus(sources, original, references) == full_o
        assert corpus(sources, ablated, references) == full_a
        saved_o = float(scores[(scores.dataset == dataset) & (scores.prompt == prompt)].iloc[0].SARI)
        saved_a = float(scores[(scores.dataset == dataset) & (scores.prompt == prompt+"_ablated")].iloc[0].SARI)
        assert round(full_o, 2) == saved_o and round(full_a, 2) == saved_a
        observed = full_a - full_o
        print(f"START {dataset} {prompt}: delta={observed:.6f}", flush=True)
        rng = np.random.default_rng(seeds[2*config_index])
        distribution = np.empty(BOOTSTRAPS)
        for b in range(BOOTSTRAPS):
            indexes = rng.integers(0, n, size=n)
            src = [sources[i] for i in indexes]
            refs = [references[i] for i in indexes]
            distribution[b] = corpus(src, [ablated[i] for i in indexes], refs) - corpus(src, [original[i] for i in indexes], refs)
        ci_low, ci_high = np.percentile(distribution, [2.5, 97.5])
        rng = np.random.default_rng(seeds[2*config_index+1])
        extreme = 0
        for b in range(PERMUTATIONS):
            swaps = rng.integers(0, 2, size=n)
            first = [ablated[i] if swaps[i] else original[i] for i in range(n)]
            second = [original[i] if swaps[i] else ablated[i] for i in range(n)]
            permuted = corpus(sources, first, references) - corpus(sources, second, references)
            extreme += abs(permuted) >= abs(observed) - 1e-12
        p_value = (extreme+1)/(PERMUTATIONS+1)
        result = {"dataset": dataset, "prompt": prompt, "n": n,
                  "original_SARI": full_o, "ablated_SARI": full_a, "delta_SARI": observed,
                  "ci95_low": float(ci_low), "ci95_high": float(ci_high),
                  "p_two_sided": p_value,
                  "baseline_SARI": float(scores[(scores.dataset == dataset)&(scores.prompt == "minimal")].iloc[0].SARI)}
        comparisons.append(result)
        np.save(destination / f"{dataset}_{prompt}_bootstrap.npy", distribution)
        pd.DataFrame({"dataset":dataset,"prompt":prompt,"row_index":range(n),
                      "text_id":[r["text_id"] for r in original_rows],"source":sources,
                      "original_output":original,"ablated_output":ablated,
                      "references_json":[json.dumps(r, ensure_ascii=False) for r in references],
                      "original_SARI":[corpus([s],[p],[r]) for s,p,r in zip(sources,original,references)],
                      "ablated_SARI":[corpus([s],[p],[r]) for s,p,r in zip(sources,ablated,references)]
                      }).to_csv(destination / f"{dataset}_{prompt}_paired_items.csv",index=False)
        print(f"DONE {result}",flush=True)
        pd.DataFrame(comparisons).to_csv(destination/"sari_comparisons_partial.csv",index=False)
    # Holm step-down familywise correction for the six prespecified tests.
    order = np.argsort([r["p_two_sided"] for r in comparisons])
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(comparisons)-rank)*comparisons[i]["p_two_sided"])
        comparisons[i]["p_holm"] = min(1.0, running)
    pd.DataFrame(comparisons).to_csv(destination/"sari_comparisons.csv",index=False)
    method={"seed":SEED,"rng":"numpy default_rng; SeedSequence(42).spawn(12); independent bootstrap/permutation streams per comparison",
            "bootstrap_replicates":BOOTSTRAPS,"ci":"paired item percentile bootstrap, pointwise 95%, not simultaneous",
            "permutations":PERMUTATIONS,"p_value":"two-sided within-item swaps; (extreme+1)/(B+1); Holm over six tests",
            "corpus_computation":"raw installed SARI _compute executed twice on every resampled dataset; exact deterministic normalize/SARIsent calls cached; public API full-score agreement asserted",
            "sari_module_sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
            "precision":"unrounded SARI for inference, original two-decimal corpus scores checked",
            "truncated_outputs":"retained, no filtering","unit":"test row; same ordered indexes in each pair",
            "limitations":"single deterministic runs; conditional on models/prompts/test items; non-significance is not equivalence; PLABA IDs repeat so row-independent resampling does not model within-document dependence",
            "elapsed_seconds":time.perf_counter()-started,"results":comparisons}
    (destination/"methodology.json").write_text(json.dumps(method,indent=2),encoding="utf-8")
    print("COMPLETE",flush=True)


if __name__ == "__main__":
    main()
