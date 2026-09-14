from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import re

def load_dataset(
    dataset_path: Path,
    id_col: str,
    source_col: str,
    ref_col: str,
    head_n: int | None = None,
    show_dataset_info: bool = True,
) -> pd.DataFrame:

    df = pd.read_csv(dataset_path)

    required = [id_col, source_col, ref_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas {missing} en {dataset_path}. "
            f"Columnas disponibles: {list(df.columns)[:30]}"
        )

    if head_n is not None and head_n > 0:
        df = df.head(head_n).copy()

    if show_dataset_info:
        print(f"CSV cargado: {dataset_path}")
        print("shape:", df.shape)
        print(df.head())

    return df


def load_prompt(prompt_path: str) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"No se encontró el prompt: {prompt_path}")
    instrucciones = prompt_path.read_text(encoding="utf-8")
    return instrucciones


def build_output_path(
    outputs_dir: Path,
    model_name: str,
    dataset_name: str,
    prompt_type: str,
    strategy: str,
    sampling_method: str,
) -> Path:
    model_short = model_name.split("/")[-1]
    model_short = re.sub(r"[:.]+", "_", model_short)
    model_family = model_short.lower().split("_")[0]
    if model_family.startswith("llama"):
        model_family = "llama"
    model_outputs_dir = outputs_dir / model_family
    model_outputs_dir.mkdir(parents=True, exist_ok=True)

    if strategy == "few":
        filename = f"predictions_{model_short}_{dataset_name}_{prompt_type}_{strategy}_{sampling_method}.csv"
    else:
        filename = f"predictions_{model_short}_{dataset_name}_{prompt_type}_{strategy}.csv"

    return model_outputs_dir / filename


def initialize_output_csv(
    df: pd.DataFrame,
    out_path: Path,
    extra_columns: list[str] | None = None,
) -> None:
    df_empty = df.head(0).copy()
    df_empty["prediction"] = pd.Series(dtype="object")
    for column in extra_columns or []:
        df_empty[column] = pd.Series(dtype="object")
    df_empty.to_csv(out_path, index=False)


def append_prediction(
    out_path: Path,
    row: pd.Series,
    prediction: str,
    extra_values: Dict[str, Any] | None = None,
) -> None:
    df_row = row.to_frame().T.copy()
    df_row["prediction"] = prediction
    for column, value in (extra_values or {}).items():
        df_row[column] = value
    df_row.to_csv(out_path, mode="a", header=False, index=False)


def save_outputs(
    df: pd.DataFrame,
    predictions: List[str],
    metadata_rows: List[Dict[str, Any]] | None,
    outputs_dir: Path,
    model_name: str,
    dataset_name: str,
    prompt_type: str,
    strategy: str,
    sampling_method: str,
) -> Path:
    print("Guardando resultados...")
    df_final = df.copy()
    df_final["prediction"] = predictions
    for metadata in metadata_rows or []:
        for column in metadata:
            if column not in df_final.columns:
                df_final[column] = pd.Series(dtype="object")
    for i, metadata in enumerate(metadata_rows or []):
        for column, value in metadata.items():
            df_final.at[df_final.index[i], column] = value
    model_short = model_name.split("/")[-1]
    print(f"Modelo corto: {model_short}")
    out_path = build_output_path(
        outputs_dir=outputs_dir,
        model_name=model_name,
        dataset_name=dataset_name,
        prompt_type=prompt_type,
        strategy=strategy,
        sampling_method=sampling_method,
    )
    print(out_path)
    df_final.to_csv(out_path, index=False)
    print("Guardado:", out_path)
    return out_path
