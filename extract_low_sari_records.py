from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = Path("outputs")
DEFAULT_OUTPUT_DIR = Path("error_analysis")
DEFAULT_PATTERN = "predictions_*.csv"
DEFAULT_METRIC_COL = "SARI"
DEFAULT_TOP_N = 15
DATASETS = ("cochrane", "plaba", "tsar2025")
TSAR_REFERENCES_PATH = PROJECT_DIR / "data" / "tsar2025" / "tsar2025_test_200.csv"


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_DIR / path


def iter_prediction_files(input_path: Path, pattern: str, recursive: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    globber = input_path.rglob if recursive else input_path.glob
    return sorted(
        path
        for path in globber(pattern)
        if path.is_file() and path.name.startswith("predictions_") and path.suffix == ".csv"
    )


def dataset_from_filename(input_path: Path) -> str:
    filename = input_path.name.lower()
    for dataset in DATASETS:
        if f"_{dataset}_" in filename:
            return dataset

    raise ValueError(
        f"No se pudo detectar el dataset en {input_path.name!r}. "
        f"Datasets esperados: {', '.join(DATASETS)}"
    )


def output_path_for(input_path: Path, output_dir: Path) -> Path:
    model_dir = input_path.parent.name
    dataset_dir = dataset_from_filename(input_path)
    return output_dir / model_dir / dataset_dir / f"{input_path.stem}_lowest_sari.json"


def select_lowest_sari(
    df: pd.DataFrame,
    metric_col: str,
    top_n: int,
) -> pd.DataFrame:
    if metric_col not in df.columns:
        raise ValueError(
            f"Falta la columna {metric_col!r}. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    scored = df.copy()
    scored[metric_col] = pd.to_numeric(scored[metric_col], errors="coerce")
    scored = scored.dropna(subset=[metric_col])

    if scored.empty:
        raise ValueError(f"No hay valores numericos validos en {metric_col!r}.")

    return scored.nsmallest(top_n, metric_col)


def load_tsar_references(path: Path = TSAR_REFERENCES_PATH) -> pd.DataFrame:
    references = pd.read_csv(path)
    references["base_text_id"] = references["text_id"].astype(str).str.split("-").str[0]
    references["target_cefr"] = references["target_cefr"].astype(str).str.upper()

    rows = []
    for base_text_id, group in references.groupby("base_text_id", sort=False):
        row = {
            "base_text_id": base_text_id,
            "original": group["original"].iloc[0],
            "reference_a2": None,
            "reference_b1": None,
        }
        for _, ref_row in group.iterrows():
            if ref_row["target_cefr"] == "A2":
                row["reference_a2"] = ref_row["reference"]
            elif ref_row["target_cefr"] == "B1":
                row["reference_b1"] = ref_row["reference"]
        rows.append(row)

    return pd.DataFrame(rows)


def enrich_tsar_references(selected: pd.DataFrame) -> pd.DataFrame:
    tsar_references = load_tsar_references()
    enriched = selected.copy()
    enriched["base_text_id"] = enriched["text_id"].astype(str)
    enriched = enriched.merge(tsar_references, on="base_text_id", how="left")
    enriched = enriched.drop(columns=["base_text_id"])

    preferred_order = [
        "text_id",
        "original",
        "reference_a2",
        "reference_b1",
        "prediction",
    ]
    remaining = [col for col in enriched.columns if col not in preferred_order]
    return enriched[[col for col in preferred_order if col in enriched.columns] + remaining]


def process_file(
    input_path: Path,
    output_dir: Path,
    metric_col: str,
    top_n: int,
) -> Path:
    df = pd.read_csv(input_path)
    selected = select_lowest_sari(df=df, metric_col=metric_col, top_n=top_n)
    if dataset_from_filename(input_path) == "tsar2025":
        selected = enrich_tsar_references(selected)

    out_path = output_path_for(input_path, output_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_json(out_path, orient="records", indent=2, force_ascii=False)

    print(
        f"{input_path.name}: seleccionados {len(selected)} registros "
        f"con menor {metric_col} -> {out_path}"
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extrae los registros con menor SARI de cada CSV predictions_*.csv "
            "y guarda un JSON por fichero con las mismas columnas del CSV."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="CSV concreto o carpeta con ficheros predictions_*.csv.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Carpeta donde se guardaran los JSON generados.",
    )
    parser.add_argument("--pattern", type=str, default=DEFAULT_PATTERN)
    parser.add_argument("--metric", type=str, default=DEFAULT_METRIC_COL)
    parser.add_argument("--top_n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--no_recursive", action="store_true")
    args = parser.parse_args()

    if args.top_n < 1:
        raise ValueError("--top_n debe ser mayor o igual que 1.")

    input_path = resolve_project_path(args.input)
    output_dir = resolve_project_path(args.output_dir)
    files = iter_prediction_files(
        input_path=input_path,
        pattern=args.pattern,
        recursive=not args.no_recursive,
    )

    if not files:
        print(f"No se encontraron ficheros de predicciones en {input_path}.")
        return

    print(f"Ficheros encontrados: {len(files)}")
    print(f"Los JSON se guardaran en: {output_dir}")
    for pred_path in files:
        try:
            process_file(
                input_path=pred_path,
                output_dir=output_dir,
                metric_col=args.metric,
                top_n=args.top_n,
            )
        except Exception as exc:
            print(f"Saltando {pred_path}: {exc}")


if __name__ == "__main__":
    main()
