from __future__ import annotations

import csv
import html
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path("outputs")
REPORT_DIR = Path("error_analysis_candidates_512")
OUT_HTML = REPORT_DIR / "systematic_error_analysis_512.html"
OUT_FLAGS = REPORT_DIR / "systematic_error_flags_512.csv"
OUT_SUMMARY = REPORT_DIR / "systematic_error_summary_512.csv"


PROMPT_TYPES = ("iso_examples", "minimal", "iso")
STRATEGY_RE = re.compile(r"_(zero|one|few)(?:_(random|metric))?\.csv$")
INTRO_RE = re.compile(
    r"\b(here is|here's|simplified text|rewritten text|note:|i have rewritten|i followed|following the instructions)\b",
    re.IGNORECASE,
)
LABEL_RE = re.compile(
    r"\b(original text|simplified text|target text|example\s*\d+|introduction:|aim:|method:|methods:|results:|conclusion:)\b",
    re.IGNORECASE,
)
LIST_RE = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+")
NUMERIC_END_RE = re.compile(
    r"(?:\b\d{1,3}(?:,\d{0,2})?$|\b\d{4}\s*(?:-|to|and)?\s*\d?$|\bCOVID-?1$|\bCovid-?1$|\bnon-Covid-?1$|\b20,00$|\b10,00$|\bover\s+\d[\d,]*$|\bfrom\s+\w+\s+\d$)",
    re.IGNORECASE,
)
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
STAT_RE = re.compile(
    r"\b(?:RR|OR|HR|CI|MD|RCTs?|p[- ]?value|I2|95%|randomi[sz]ed|placebo|meta-analys\w*)\b",
    re.IGNORECASE,
)
BIOMED_TERMS_RE = re.compile(
    r"\b(?:hCG|ferritin|deferiprone|deferasirox|deferoxamine|hypoglycemia|ectopic|insulin|naltrexone|anaesthesia|ultrasound|hyperemesis|molar|chemotherapy|SARS-CoV-2|COVID-19|lupus|biomarker|myeloablative|pneumonitis|veno-occlusive)\b",
    re.IGNORECASE,
)


def parse_metadata(path: Path) -> dict[str, str]:
    stem = path.stem
    if not stem.startswith("predictions_"):
        raise ValueError(f"Not a predictions file: {path}")

    model = "llama_3.1_8B" if "llama3_1_8b" in stem else "mixtral_8x7B"
    dataset = next((name for name in ("cochrane", "plaba", "tsar2025") if f"_{name}_" in stem), "unknown")
    prompt_type = next((p for p in PROMPT_TYPES if f"_{p}_" in stem), "unknown")

    match = STRATEGY_RE.search(path.name)
    if not match:
        strategy = "unknown"
        sampling = "-"
    else:
        strategy = match.group(1)
        sampling = match.group(2) or "-"

    return {
        "model": model,
        "dataset": dataset,
        "prompt_type": prompt_type.replace("iso_examples", "ISO+examples").replace("iso", "ISO"),
        "strategy": strategy,
        "sampling": sampling,
    }


def as_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def short_text(value: str, chars: int = 220) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= chars:
        return text
    return text[: chars - 1].rstrip() + "..."


def has_technical_markers(dataset: str, prediction: str) -> bool:
    if dataset not in {"cochrane", "plaba"}:
        return False
    acronyms = [x for x in ACRONYM_RE.findall(prediction) if x not in {"We", "IV"}]
    return bool(STAT_RE.search(prediction) or BIOMED_TERMS_RE.search(prediction) or len(acronyms) >= 3)


def classify_row(meta: dict[str, str], row: dict[str, str]) -> dict[str, object]:
    prediction = row.get("prediction", "") or ""
    stripped = prediction.strip()
    len_pred = as_float(row.get("LEN_PRED", "0"))
    len_ref = as_float(row.get("LEN_REF", "0"))
    done_reason = (row.get("done_reason", "") or "").strip()

    empty = stripped == ""
    reached_limit = done_reason == "length"
    very_short = len_ref > 0 and len_pred < (0.5 * len_ref)
    abrupt_stop = (
        not empty
        and done_reason == "stop"
        and (NUMERIC_END_RE.search(stripped) is not None or (len_pred <= 10 and stripped[-1:] not in ".!?"))
    )
    format_related = INTRO_RE.search(prediction) is not None or LABEL_RE.search(prediction) is not None
    list_like = len(LIST_RE.findall(prediction)) >= 2
    technical = has_technical_markers(meta["dataset"], prediction)

    flags = {
        "empty_prediction": empty,
        "reached_generation_limit": reached_limit,
        "too_brief_vs_reference": very_short,
        "ended_abruptly": abrupt_stop,
        "format_related_marker": format_related,
        "list_like_format": list_like,
        "technical_or_statistical_markers": technical,
    }
    any_flag = any(flags.values())

    return {
        **meta,
        "text_id": row.get("text_id", ""),
        "len_pred": len_pred,
        "len_ref": len_ref,
        "sari": as_float(row.get("SARI", "")),
        "done_reason": done_reason,
        **{name: int(value) for name, value in flags.items()},
        "any_flag": int(any_flag),
        "prediction_excerpt": short_text(prediction),
    }


def summarize(records: list[dict[str, object]], fields: tuple[str, ...]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[tuple(record[field] for field in fields)].append(record)

    rows = []
    flag_names = [
        "empty_prediction",
        "reached_generation_limit",
        "too_brief_vs_reference",
        "ended_abruptly",
        "format_related_marker",
        "list_like_format",
        "technical_or_statistical_markers",
        "any_flag",
    ]
    for key, items in sorted(groups.items()):
        row = {field: value for field, value in zip(fields, key)}
        row["n"] = len(items)
        row["avg_pred_words"] = round(mean(float(x["len_pred"]) for x in items), 2)
        row["avg_ref_words"] = round(mean(float(x["len_ref"]) for x in items), 2)
        row["avg_sari"] = round(mean(float(x["sari"]) for x in items), 2)
        for flag in flag_names:
            count = sum(int(x[flag]) for x in items)
            row[f"{flag}_n"] = count
            row[f"{flag}_pct"] = round(100 * count / len(items), 2)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def html_table(rows: list[dict[str, object]], columns: list[str], max_rows: int | None = None) -> str:
    rows = rows if max_rows is None else rows[:max_rows]
    head = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def make_html(records: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> str:
    summary_cols = [
        "group",
        "n",
        "avg_pred_words",
        "avg_ref_words",
        "avg_sari",
        "too_brief_vs_reference_n",
        "too_brief_vs_reference_pct",
        "ended_abruptly_n",
        "ended_abruptly_pct",
        "format_related_marker_n",
        "format_related_marker_pct",
        "technical_or_statistical_markers_n",
        "technical_or_statistical_markers_pct",
        "reached_generation_limit_n",
        "reached_generation_limit_pct",
        "any_flag_n",
        "any_flag_pct",
    ]
    example_cols = [
        "model",
        "dataset",
        "prompt_type",
        "strategy",
        "sampling",
        "text_id",
        "len_pred",
        "len_ref",
        "sari",
        "done_reason",
        "triggered_flags",
        "prediction_excerpt",
    ]

    sections = []
    for title, field in [
        ("By Model", "model"),
        ("By Dataset", "dataset"),
        ("By Prompt Type", "prompt_type"),
        ("By Zero/One/Few Configuration", "strategy"),
        ("By Example Selection Method", "sampling"),
        ("By Model and Dataset", "model_dataset"),
        ("By Model, Dataset, and Prompt Type", "model_dataset_prompt"),
        ("By Model, Dataset, Prompt Type, and Configuration", "full_setting"),
    ]:
        rows = [r for r in summary_rows if r["summary_level"] == field]
        sections.append(f"<section><h2>{html.escape(title)}</h2>{html_table(rows, summary_cols)}</section>")

    flagged = []
    flag_names = [
        "empty_prediction",
        "reached_generation_limit",
        "too_brief_vs_reference",
        "ended_abruptly",
        "format_related_marker",
        "list_like_format",
        "technical_or_statistical_markers",
    ]
    for record in records:
        names = [name for name in flag_names if int(record[name])]
        if not names:
            continue
        flagged.append({**record, "triggered_flags": ", ".join(names)})
    flagged = sorted(flagged, key=lambda x: (x["dataset"], x["model"], float(x["sari"])))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Systematic Error Analysis 512</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; margin: 32px; color: #222; line-height: 1.45; }}
    h1 {{ margin-bottom: 0.2rem; }}
    h2 {{ margin-top: 2rem; }}
    .note {{ max-width: 1100px; padding: 14px 16px; border-left: 4px solid #444; background: #f5f5f5; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #cfcfcf; padding: 7px; vertical-align: top; }}
    th {{ background: #eeeeee; text-align: left; }}
    td:last-child {{ max-width: 420px; }}
  </style>
</head>
<body>
  <h1>Systematic Error Analysis for 512-token Outputs</h1>
  <p class="note">
    This report applies simple automatic heuristics to all prediction files in <code>outputs/llama_512</code>
    and <code>outputs/mixtral_512</code>. It is intended as supporting evidence for the manual qualitative
    error analysis. The flags identify empty predictions, outputs that reached the generation limit, outputs
    that are much shorter than the references, outputs that ended abruptly, format-related markers, list-like
    formatting, and biomedical technical or statistical markers. These automatic flags should be interpreted
    as screening signals, not as final manual annotations.
  </p>
  {"".join(sections)}
  <section>
    <h2>Flagged Examples</h2>
    {html_table(flagged, example_cols, max_rows=300)}
  </section>
</body>
</html>"""


def main() -> None:
    prediction_files = []
    for subdir in (ROOT / "llama_512", ROOT / "mixtral_512"):
        prediction_files.extend(sorted(subdir.glob("predictions_*.csv")))

    records: list[dict[str, object]] = []
    for path in prediction_files:
        meta = parse_metadata(path)
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(classify_row(meta, row))

    write_csv(OUT_FLAGS, records)

    summary_specs = [
        ("model", ("model",)),
        ("dataset", ("dataset",)),
        ("prompt_type", ("prompt_type",)),
        ("strategy", ("strategy",)),
        ("sampling", ("sampling",)),
        ("model_dataset", ("model", "dataset")),
        ("model_dataset_prompt", ("model", "dataset", "prompt_type")),
        ("full_setting", ("model", "dataset", "prompt_type", "strategy", "sampling")),
    ]
    all_summaries = []
    for level, fields in summary_specs:
        for row in summarize(records, fields):
            row["summary_level"] = level
            row["group"] = " / ".join(str(row[field]) for field in fields)
            all_summaries.append(row)

    write_csv(OUT_SUMMARY, all_summaries)
    OUT_HTML.write_text(make_html(records, all_summaries), encoding="utf-8")
    print(f"Wrote {OUT_HTML.resolve()}")
    print(f"Wrote {OUT_FLAGS.resolve()}")
    print(f"Wrote {OUT_SUMMARY.resolve()}")


if __name__ == "__main__":
    main()
