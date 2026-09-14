from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import sacrebleu
from eval_utils import compute_bertscore, compute_meaningbert, compute_sari, evaluate_predictions
from evaluate_all import load_data_tsar
import textstat

COL_ID = "text_id"
COL_COMPLEX = "original"
COL_REFERENCE = "reference"
COL_PREDICTION = "prediction"


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def text_len(text):
    return len(str(text).split())

def mean_ref_len(refs):
    """
    refs puede ser:
    - una string
    - una lista de referencias
    """
    if isinstance(refs, list):
        lens = [text_len(r) for r in refs]
        return sum(lens) / len(lens) if lens else 0

    return text_len(refs)


def compute_sentence_bleu(prediction, references):
    prediction_text = str(prediction).strip()
    if isinstance(references, list):
        reference_texts = [str(ref).strip() for ref in references if str(ref).strip()]
    else:
        reference_texts = [str(references).strip()]

    if not prediction_text or not reference_texts:
        return 0.0

    return round(float(sacrebleu.sentence_bleu(prediction_text, reference_texts).score), 2)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anade columnas SARI y BERTScore F1 a los CSV de predicciones."
    )
    parser.add_argument("--outputs_dir", type=Path, default=Path("outputs"))
    parser.add_argument("--pattern", type=str, default="predictions_*.csv")
    parser.add_argument("--lang", type=str, default="en")
    parser.add_argument("--eval_semantic", type=str_to_bool, default=True, help="Si se deben evaluar las métricas semánticas (BERTScore, MeaningBERT).")
    parser.add_argument("--force", default=True, help="Recalcula aunque las columnas ya existan.")
    parser.add_argument(
        "--sari_method",
        choices=["legacy", "standard", "auto"],
        default="standard",
        help="legacy usa la implementacion antigua; standard usa evaluate.load('sari'); auto intenta standard y cae a legacy.",
    )
    args = parser.parse_args()

   

    files = sorted(
        path for path in args.outputs_dir.rglob(args.pattern)
        if not any("backup" in part.lower() for part in path.parts)
    )
    if not files:
        print("No se encontraron ficheros de predicciones.")
        return

    print(f"Ficheros encontrados: {len(files)}")
    for pred_path in files:
        df = pd.read_csv(pred_path, keep_default_na=False)
        #print(df.columns)
        if args.force:
            print(f"Procesando {pred_path}...")
            if "_tsar2025_" not in pred_path.name:  
                sources = df[COL_COMPLEX].astype(str).tolist()
                references = df[COL_REFERENCE].astype(str).tolist()
                predictions = df[COL_PREDICTION].astype(str).tolist()
                references_bleu = None
                metric_cols = {"LEN_COMPLEX", "LEN_PRED", "LEN_REF", "BLEU", "SARI", "FKGL", "FRE", "BERTScore-F1", "MeaningBERT"}
                extra_cols = [col for col in df.columns if col not in {COL_ID, COL_COMPLEX, COL_REFERENCE, COL_PREDICTION, *metric_cols}]
                df = df[[COL_ID, COL_COMPLEX, COL_REFERENCE, COL_PREDICTION, *extra_cols]]
            else:
                predictions, sources, references, references_bleu, _ = load_data_tsar(pred_path, Path("data/tsar2025/tsar2025_test_200.csv"))
                metric_cols = {"LEN_COMPLEX", "LEN_PRED", "LEN_REF", "BLEU", "SARI", "FKGL", "FRE", "BERTScore-F1", "MeaningBERT"}
                extra_cols = [col for col in df.columns if col not in {COL_ID, COL_PREDICTION, *metric_cols}]
                df = df[[COL_ID, COL_PREDICTION, *extra_cols]]
            
            df["LEN_COMPLEX"] = [text_len(s) for s in sources]
            df["LEN_PRED"] = [text_len(p) for p in predictions]
            df["LEN_REF"] = [mean_ref_len(r) for r in references]

            df["BLEU"] = [
                compute_sentence_bleu(pred, ref)
                for pred, ref in zip(predictions, references)
            ]
            df["SARI"] = [
                compute_sari([src], [pred], [ref], method=args.sari_method)
                for src, pred, ref in zip(sources, predictions, references)
            ]
            df["FKGL"] = [round(float(textstat.flesch_kincaid_grade(pred)), 2) for pred in predictions]
            df["FRE"] = [round(float(textstat.flesch_reading_ease(pred)), 2) for pred in predictions]

            print(args.eval_semantic)
            if args.eval_semantic:
                bert_scores = compute_bertscore(predictions, references, lang=args.lang, return_mean=False)
                df["BERTScore-F1"] = bert_scores["BERTScore-F1"]
                meaningbert_scores = compute_meaningbert(predictions, sources, return_mean=False)
                df["MeaningBERT"] = meaningbert_scores
            # print(df.head())
            # Reescribir CSV
            df.to_csv(pred_path, index=False)
            print(f"Archivo actualizado: {pred_path}")

        else:
            print(f"Archivo {pred_path} ya tiene métricas calculadas. Use --force para recalcular.")
            continue



if __name__ == "__main__":
    main()
