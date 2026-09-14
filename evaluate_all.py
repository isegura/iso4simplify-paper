from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
from eval_utils import evaluate_predictions

COL_ID = "text_id"
COL_COMPLEX = "original"
COL_REFERENCE = "reference"
COL_PREDICTION = "prediction"

VALID_MODELS = {"llama3_1_8b", "mixtral_latest"}

VALID_DATASETS = {"tsar2025", "cochrane", "plaba"}
VALID_PROMPT_TYPES = {"minimal", "iso", "iso_examples"}
VALID_STRATEGIES = {"zero", "one", "few"}

VALID_SAMPLING_METHODS = {"random", "metric"}
VALID_STRATEGIES= {"zero", "one", "few"}

VALID_PROMPT_TYPES= {"minimal", "iso", "iso_examples"}
VALID_DATASETS = {"cochrane", "plaba", "tsar2025"}

def extract_last(parts, valid_values):
    for i in range(1, len(parts) + 1):
        candidate = "_".join(parts[-i:])
        if candidate in valid_values:
            del parts[-i:]
            return candidate
    return None


def parse_prediction_filename(filename):

    parts = Path(filename).stem.removeprefix("predictions_").split("_")

    sampling_method = extract_last(parts, VALID_SAMPLING_METHODS)
    strategy = extract_last(parts, VALID_STRATEGIES)
    prompt_type = extract_last(parts, VALID_PROMPT_TYPES)
    dataset_name = extract_last(parts, VALID_DATASETS)

    model_name = "_".join(parts)

    return {
        "model_name": model_name,
        "dataset_name": dataset_name,
        "prompt_type": prompt_type,
        "strategy": strategy,
        "sampling_method": sampling_method,
    }




def load_data_tsar(
    pred_file: Path,
    gold_file: Path
) -> tuple[list[str], list[str], list[list[str]], list[list[str]], pd.DataFrame]:

    df_pred = pd.read_csv(pred_file, keep_default_na=False)
    df_gold = pd.read_csv(gold_file, keep_default_na=False)

    df_pred["base_id"] = df_pred["text_id"].astype(str)
    df_gold["base_id"] = df_gold["text_id"].astype(str).str.extract(r"^(\d+)")

    df_refs = (
        df_gold
        .groupby("base_id")
        .agg(
            source=("original", "first"),
            references=("reference", list)
        )
        .reset_index()
    )

    df_eval = df_pred.merge(df_refs, on="base_id", how="inner")
    predictions = df_eval["prediction"].astype(str).tolist()
    sources = df_eval["source"].astype(str).tolist()

    # Para SARI y BERTScore
    references = df_eval["references"].tolist()
    # print("References sample:", references[0])
    # Para BLEU con sacrebleu
    references_multi_bleu = list(map(list, zip(*references)))
    # print("References bleu sample:", references_bleu[0])
    
    return predictions, sources, references, references_multi_bleu, df_eval




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions_dir", type=str, default="outputs")
    parser.add_argument("--scores_dir", type=str, default="scores")
    parser.add_argument("--lang", type=str, default="en")
    parser.add_argument("--pattern", type=str, default="predictions_*.csv")
    parser.add_argument("--eval_semantic", type=bool, default=True, help="Si se deben evaluar las métricas semánticas (BERTScore, MeaningBERT).")
    parser.add_argument("--overwrite", type=bool, default=False, help="Sobreescribir archivos de puntuación existentes.")
    parser.add_argument(
        "--sari_method",
        choices=["legacy", "standard", "auto"],
        default="standard",
        help="legacy usa la implementacion antigua; standard usa evaluate.load('sari'); auto intenta standard y cae a legacy.",
    )

    args = parser.parse_args()

    predictions_dir = Path(args.predictions_dir)
    scores_dir = Path(args.scores_dir)
    scores_dir.mkdir(parents=True, exist_ok=True)

    gold_tsar2025= Path("data/tsar2025/tsar2025_test_200.csv")

    files = sorted(
        p for p in predictions_dir.rglob(args.pattern)
        if not any("backup" in part.lower() for part in p.parts)
    )

    print(f"Número total de ficheros a evaluar: {len(files)}")
    print("Evaluating semantic:", args.eval_semantic)
    if not files:
        print("No se encontraron archivos de predicciones.")
        return

    all_scores = []

    for pred_file in files:
        print(f"\nEvaluating {pred_file.name}...")
        metadata = parse_prediction_filename(pred_file.name)
        metadata["lang"] = args.lang
        metadata["sari_method"] = args.sari_method
        print(f"Parsed metadata: {metadata}")
        dataset = metadata["dataset_name"]
        
        # ruta relativa respecto a outputs/
        rel_path = pred_file.relative_to(predictions_dir)

        # cambiar nombre del archivo
        score_filename = rel_path.with_name(
            rel_path.stem.replace("predictions_", "scores_") + ".csv"
        )

        # ruta final dentro de scores/
        score_file = scores_dir / score_filename

        # crear subcarpetas si no existen
        score_file.parent.mkdir(parents=True, exist_ok=True)

        print("Saving to:", score_file)


        print(f"Score file: {score_file.name}")
        if args.overwrite or not score_file.exists():
            if dataset != "tsar2025":
                df = pd.read_csv(pred_file, keep_default_na=False)
                sources = df[COL_COMPLEX].astype(str).tolist()
                references = df[COL_REFERENCE].astype(str).tolist()
                predictions = df[COL_PREDICTION].astype(str).tolist()
                references_bleu = None
            else:
                predictions, sources, references, references_bleu, _ = load_data_tsar(pred_file, gold_tsar2025)
            scores = evaluate_predictions(
                predictions,
                sources,
                references,
                references_bleu,
                lang=args.lang,
                eval_semantic=args.eval_semantic,
                sari_method=args.sari_method,
            )
            df_score = pd.DataFrame([scores])
            df_score.to_csv(score_file, index=False)
            print(f"Scores saved to {score_file.name}: {scores}")  
        else:
            print(f"Score file already exists and overwrite is False. Loading scores from {score_file.name}...")
            df_score = pd.read_csv(score_file)

        df_score = pd.concat([pd.DataFrame([metadata]), df_score], axis=1)
        all_scores.append(df_score)
        
    df_all_scores = pd.concat(all_scores, ignore_index=True)
    final_path = scores_dir / f"all_scores.csv"
    df_all_scores.to_csv(final_path, index=False)
    print(f"\nResultados agregados guardados en: {final_path}")


if __name__ == "__main__":
    main()
