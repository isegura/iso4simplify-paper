"""Complete paired item deliverables; never modify inference CSVs."""
from focused_metric_runtime import configure, ROOT, BASE
configure()
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import textstat
from eval_utils import compute_bertscore, compute_meaningbert
from add_prediction_metrics import compute_sentence_bleu
from run_focused_ablation import EXPECTED


def main():
    dest = BASE / "per_item"
    dest.mkdir(exist_ok=True)
    combined = []
    for dataset, n in EXPECTED.items():
        for prompt in ("iso", "iso_examples"):
            checkpoint = dest / f"{dataset}_{prompt}_comparison.csv"
            pair_path = BASE / "statistics" / f"{dataset}_{prompt}_paired_items.csv"
            original_path = ROOT / "outputs/llama_512" / f"predictions_llama3_1_8b_{dataset}_{prompt}_zero.csv"
            new_path = BASE / "predictions/llama" / f"predictions_llama3_1_8b_{dataset}_{prompt}_ablated_zero.csv"
            if checkpoint.exists():
                raise FileExistsError(f"Refusing to overwrite {checkpoint}")
            frame = pd.read_csv(pair_path, keep_default_na=False)
            original = pd.read_csv(original_path, keep_default_na=False)
            new = pd.read_csv(new_path, keep_default_na=False)
            assert len(frame) == n
            assert frame.original_output.tolist() == original.prediction.tolist()
            assert frame.ablated_output.tolist() == new.prediction.tolist()
            refs = [json.loads(r) for r in frame.references_json]
            predictions = frame.ablated_output.tolist()
            print(f"START {dataset} {prompt}",flush=True)
            frame["ablated_BERTScore-F1"] = compute_bertscore(predictions, refs, lang="en", return_mean=False)["BERTScore-F1"]
            frame["ablated_MeaningBERT"] = compute_meaningbert(predictions, frame.source.tolist(), return_mean=False)
            for metric in ("BERTScore-F1", "MeaningBERT"):
                frame["original_"+metric] = pd.to_numeric(original[metric])
            for variant, output_frame in (("original",original),("ablated",new)):
                outputs = frame[variant+"_output"].tolist()
                frame[variant+"_BLEU_sentence"] = [compute_sentence_bleu(p,r) for p,r in zip(outputs,refs)]
                frame[variant+"_FKGL"] = [round(float(textstat.flesch_kincaid_grade(p)),2) for p in outputs]
                frame[variant+"_FRE"] = [round(float(textstat.flesch_reading_ease(p)),2) for p in outputs]
                descriptive = pd.read_csv(BASE/"evaluation"/f"{dataset}_{prompt+('_ablated' if variant=='ablated' else '')}_descriptive_items.csv")
                assert descriptive.row_index.tolist() == frame.row_index.tolist()
                for metric in ("output_length","compression_ratio","copy_rate"):
                    frame[variant+"_"+metric] = descriptive[metric].tolist()
                frame[variant+"_done_reason"] = output_frame.done_reason.tolist()
            frame["delta_SARI"] = frame.ablated_SARI - frame.original_SARI
            assert np.isfinite(frame.select_dtypes(include="number").to_numpy()).all()
            frame.to_csv(checkpoint,index=False)
            combined.append(frame)
            print(f"DONE {dataset} {prompt}",flush=True)
    pd.concat(combined,ignore_index=True).to_csv(dest/"all_paired_items.csv",index=False)
    (dest/"methodology.json").write_text(json.dumps({
        "comparisons":6,"paired_rows":sum(len(f) for f in combined),
        "SARI":"raw standard metric per item from paired analysis",
        "BLEU_sentence":"sacrebleu.sentence_bleu, same helper as existing item evaluation; not corpus BLEU",
        "semantic_original":"existing original prediction item columns, aligned by row; aggregate reproduction already verified",
        "semantic_ablated":"existing eval_utils item functions; pinned MeaningBERT",
        "readability":"textstat per-item, existing two-decimal convention",
        "additional":"same per-item definitions as completed aggregate evaluation",
        "rounding":"per-item semantic/readability rounding follows existing code; averages may differ slightly from separately rounded aggregate scores",
        "prediction_files":"read only; no originals or ablations rewritten"
    },indent=2),encoding="utf-8")
    print("COMPLETE",flush=True)


if __name__ == "__main__":
    main()
