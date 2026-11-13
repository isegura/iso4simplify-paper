"""Combine completed Llama and Mixtral artifacts without rerunning metrics."""
from pathlib import Path
import json
import csv
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "experiments/focused_ablation"
DEST = BASE / "combined"


def table(records, columns):
    lines = ["| " + " | ".join(label for key,label,fmt in columns) + " |",
             "|" + "---|" * len(columns)]
    for record in records:
        lines.append("| " + " | ".join(format(float(record[key]),fmt) if fmt else str(record[key])
                                     for key,label,fmt in columns) + " |")
    return "\n".join(lines)


def main():
    DEST.mkdir(exist_ok=True)
    statistics, aggregates, items, truncation = [], [], [], []
    for model, folder, original_folder, model_short in (
        ("Llama 3.1 8B",BASE,"llama_512","llama3_1_8b"),
        ("Mixtral 8x7B",BASE/"mixtral","mixtral_512","mixtral_latest")):
        assert json.loads((folder/"evaluation/complete.json").read_text())["configurations"]==15
        check=pd.read_csv(folder/"evaluation/original_score_check.csv")
        assert len(check)==54 and (check.delta==0).all()
        stats=pd.read_csv(folder/"statistics/sari_comparisons.csv")
        assert len(stats)==6
        stats.insert(0,"model",model)
        stats.rename(columns={"p_holm":"p_holm_within_model"},inplace=True)
        statistics.append(stats)
        aggregate=pd.read_csv(folder/"evaluation/all_metrics.csv")
        aggregate.insert(0,"model",model);aggregates.append(aggregate)
        pair=pd.read_csv(folder/"per_item/all_paired_items.csv",keep_default_na=False)
        assert len(pair)==746
        pair.insert(0,"model",model);items.append(pair)
        for row in stats.to_dict("records"):
            d,p=row["dataset"],row["prompt"]
            original_path=ROOT/"outputs"/original_folder/f"predictions_{model_short}_{d}_{p}_zero.csv"
            ablated_path=folder/"predictions"/("llama" if model.startswith("Llama") else "mixtral")/f"predictions_{model_short}_{d}_{p}_ablated_zero.csv"
            old=pd.read_csv(original_path,keep_default_na=False)
            new=pd.read_csv(ablated_path,keep_default_na=False)
            truncation.append({"model":model,"dataset":d,"prompt":p,"n":len(old),
                "original_length_terminations":int((old.done_reason=="length").sum()),
                "ablated_length_terminations":int((new.done_reason=="length").sum())})
            dist=np.load(folder/"statistics"/f"{d}_{p}_bootstrap.npy")
            assert len(dist)==10000 and np.isfinite(dist).all()
            assert np.allclose(np.percentile(dist,[2.5,97.5]),[row["ci95_low"],row["ci95_high"]])
            subset=pair[(pair.dataset==d)&(pair.prompt==p)]
            assert len(subset)==len(new)
            assert round(subset.ablated_MeaningBERT.astype(float).mean(),2)==float(aggregate[(aggregate.dataset==d)&(aggregate.prompt==p+"_ablated")].iloc[0].MeaningBERT)
    stats=pd.concat(statistics,ignore_index=True)
    # Preserve the original six-comparison families; also report global 12-test Holm.
    order=np.argsort(stats.p_two_sided.to_numpy())
    adjusted=np.zeros(len(stats));running=0.
    for rank,index in enumerate(order):
        running=max(running,(len(stats)-rank)*float(stats.iloc[index].p_two_sided))
        adjusted[index]=min(1.,running)
    stats["p_holm_all_12"]=adjusted
    stats.to_csv(DEST/"sari_comparisons.csv",index=False)
    aggregate=pd.concat(aggregates,ignore_index=True)
    aggregate.to_csv(DEST/"all_metrics.csv",index=False)
    aggregate[aggregate.prompt.str.endswith("_ablated")].to_csv(DEST/"ablation_metrics.csv",index=False)
    pd.concat(items,ignore_index=True).to_csv(DEST/"all_paired_items.csv",index=False)
    pd.DataFrame(truncation).to_csv(DEST/"truncation_comparison.csv",index=False)
    records=stats.to_dict("records")
    for r in records:r["CI"]=f"[{r['ci95_low']:.3f}, {r['ci95_high']:.3f}]"
    comparison_table=table(records,[("model","Model",""),("dataset","Dataset",""),("prompt","Prompt",""),
        ("original_SARI","Original",".2f"),("ablated_SARI","Ablated",".2f"),("delta_SARI","Delta","+.3f"),
        ("CI","95% CI",""),("p_two_sided","p",".5f"),("p_holm_within_model","Holm (6)",".5f"),
        ("p_holm_all_12","Holm (12)",".5f")])
    metric_table=table(aggregate[aggregate.prompt.str.endswith("_ablated")].to_dict("records"),[
        ("model","Model",""),("dataset","Dataset",""),("prompt","Prompt",""),("SARI","SARI",".2f"),
        ("BLEU","BLEU",".2f"),("BERTScore-F1","BERTScore-F1",".4f"),("MeaningBERT","MeaningBERT",".2f"),
        ("FKGL","FKGL",".2f"),("FRE","FRE",".2f"),("output_length","Words",".2f"),
        ("compression_ratio","Compression",".4f"),("copy_rate","Copy rate",".4f")])
    truncation_table=table(truncation,[("model","Model",""),("dataset","Dataset",""),("prompt","Prompt",""),
        ("n","n",".0f"),("original_length_terminations","Original length",".0f"),("ablated_length_terminations","Ablated length",".0f")])
    report="""# Focused organization/summary ablation — two-model scientific report

This is the current consolidated report. The earlier Llama-only report is
retained as historical evidence. The manuscript and submission tag v1.0.3
(user-confirmed) have not been edited, committed or published.

## 1. Objective

Test the contribution of the explicit information-hierarchy, initial-summary
and logical-grouping block in the existing ISO and ISO+examples prompts,
addressing Reviewer #2 Concern #1 through the requested focused ablation.
This is not a length-matched non-ISO control and does not identify the entire
causal effect of ISO 24495-1.

## 2. Exact prompt change

The two ablated prompt files are exact byte copies outside removal of the
PRINCIPLES OF ORGANIZATION AND HIERARCHY heading and its three instructions.
See [ISO diff](../iso.diff) and [ISO+examples diff](../iso_examples.diff).
ROLE, MISSION, ISO framing, all linguistic instructions, omission permissions,
VISUAL FORMAT, RESPONSE FORMAT and all illustrative examples remain.
Baseline prompts are unchanged. In particular, lists remain requested after
ablation; the intervention does not remove every source of organization cues.

## 3. Experimental design

Two models × two ablated prompts × three datasets = 12 new zero-shot
configurations, 1,492 generated outputs. Cochrane uses 125 rows, PLABA 148,
TSAR2025 100 per configuration. Original sources/references/ordering were
checked by row, ID, source and reference. No preprocessing or postprocessing
change was introduced. All 12 executions completed without empty predictions.
Execution completeness does not establish linguistic/content completeness.

Nine original zero-shot comparator cells per model (baseline, ISO, ISO+examples
on each dataset) were recomputed, giving 30 aggregate evaluation cells total.
All 108 saved original aggregate metric values are reproduced exactly at
their reported precision. See each model's original_score_check.csv.

## 4. Model and evaluation setup

Both use Ollama with output cap 512, num_ctx 8192, temperature 0, seed 42,
top_k 1, top_p 1, repeat_penalty 1.1, repeat_last_n 64, num_gpu 999, GPU
required and timeout 900 seconds, matching the original logs. GPU-use checks
do not guarantee that all model layers fit entirely in VRAM.

- Llama: llama3.1:8b, Q4_K_M, digest
  46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e.
- Mixtral: mixtral:latest, Q4_0, digest
  a3b6bef0f836ff29ddb576a80eeb1b7def43ec9b809466f62e96adb871fe8498.
- New inference runtime: Ollama 0.40.6. Historical binary/runtime identity is
  not certified by the old logs despite matching decoding parameters.
- Evaluation: separate .venv-eval, PyTorch 2.10.0+cu128; other pinned package
  versions preserved. BERTScore uses CUDA; original MeaningBERT runs on CPU.

## 5. Metrics and inference

The six existing metric implementations are unchanged: standard evaluate SARI
(no legacy fallback), default sacrebleu corpus BLEU, English roberta-large
BERTScore-F1 without baseline rescaling, pinned earlier MeaningBERT against
the source, and mean textstat FKGL/FRE. TSAR uses A2/B1 references jointly.
MeaningBERT code and root checkpoint hashes are fixed by the shared provenance
record; the newer default model is not substituted.

Additional metrics: word count len(split()); mean per-item output/source word
ratio; mean proportion of exact case-sensitive output whitespace tokens that
occur in the source token set, punctuation retained. Copy rate is lexical
overlap on 0–1, not a verbatim phrase detector or meaning-preservation score.

Primary endpoint: unrounded SARI(ablated)−SARI(original). Each interval uses
10,000 paired percentile bootstrap samples of test rows, seed 42. Identical
sampled indexes apply to both conditions. The raw corpus implementation is
executed for both sampled datasets; only its deterministic normalization and
sentence kernel are cached. Full scores were checked against the public API.
Corpus BLEU is never estimated by averaging sentence BLEU.

Two-sided within-item randomization tests use 19,999 swaps and
(extreme+1)/(B+1). The original six-comparison Holm family for each model is
retained; an additional Holm correction across all 12 contrasts is reported.
Intervals are pointwise, not simultaneous. No model interaction or difference
between model effects has been tested. Baseline and complementary metrics are
descriptive, without additional significance claims.

## 6. Quantitative results

### Twelve ablations: nine metrics

"""+metric_table+"""

### Matched SARI comparisons

"""+comparison_table+"""

All 12 intervals include zero. No contrast rejects at 0.05 even without
multiple-comparison correction. Changes range from −0.110 to +0.769 points.
The largest point estimate is Mixtral ISO+examples on TSAR (+0.769,
CI [−0.294, 1.831], raw p=0.15575). This remains compatible with decreases
and increases and does not establish equivalence or absence of an effect.

Mixtral ISO mean length increases on all three datasets; ISO+examples length
increases on Cochrane but decreases on PLABA/TSAR. MeaningBERT decreases in
all six Mixtral ablations, whereas it increased in five Llama comparisons.
These are descriptive changes; no claim of significant meaning loss or
cross-model interaction is warranted. The full original/baseline metrics
are in [all_metrics.csv](all_metrics.csv).

The baseline ordering is model/dataset dependent: for example, Mixtral
ISO+examples on TSAR moves from 47.50 below baseline 47.66 to 48.27 above it.
That numerical crossing is not a tested improvement over baseline and should
not be promoted to one. No all-72-configuration claim follows from this study.

### Generation-cap terminations

"""+truncation_table+"""

All outputs are retained in primary analyses. In Cochrane, differential cap
termination can affect matched comparisons. No non-truncated sensitivity
analysis is claimed. A run finishing successfully and an output receiving
stop are not evidence that the text is semantically complete.

## 7. Qualitative review

Both models use the same prespecified five source positions per dataset:
Cochrane 0/31/62/93/124, PLABA 0/36/73/110/147, TSAR 0/24/49/74/99.
This yields 60 paired output comparisons over the same 15 sources, not 30
independent sources. Selection was not based on metrics or observed errors.
Full texts and case notes: [Llama review](../qualitative/QUALITATIVE_REVIEW.md)
and [Mixtral review](../mixtral/qualitative/QUALITATIVE_REVIEW.md).

Exploratory inspection found preserved chronological/source ordering and
heterogeneous segmentation. Numbered lists can appear or persist after the
block is removed: Mixtral TSAR45 ISO changes from a paragraph to five points;
Cochrane CD011655 ISO similarly becomes numbered. Original prompts also do
not consistently produce an initial standalone summary. These observations
do not isolate a mechanism; formatting instructions remain in both conditions.

Mixtral additionally shows sample outputs that end in partial numbers or
introductions with stop rather than length. Cochrane CD009601 ISO+examples
ablated ends at “Some studies compared:”; CD008053 ends at “a total of 1”.
PLABA27630909 has fragmentary outputs in both prompt families and conditions.
These are observed apparent content failures, not diagnosed token-cap events.
PLABA34477130 ISO+examples original does end with length; its ablation reaches
a conclusion with stop. Such pairs confound judgments of structure with
coverage/termination. No cause such as repeat penalty, stop sequences,
quantization or input clipping is asserted without a separate diagnostic.

This is AI-assisted exploratory inspection, not a human evaluation, an ISO
adherence rate or a population error-frequency estimate. There were no blinded
independent raters, adjudication, comprehension tasks or agreement statistics.

## 8. Limitations

- Zero-shot, two existing models and one deterministic generation per cell;
  no inference across demonstration seeds or additional models.
- Historical model/runtime identity uncertain; matching parameters alone do
  not eliminate runtime confounding across original/new generations.
- Prompt length, instruction count, omission permissions and retained format
  instructions are not jointly controlled; no length-matched non-ISO control.
- Reference-based metrics do not measure hierarchy, summary-first quality,
  compliance with ISO or usefulness to readers. No equivalence margin/test.
- Row-based PLABA resampling ignores possible shared-document dependence;
  repeated IDs were explicitly left uninvestigated by the user.
- Cochrane generation-cap rates differ, and stop can accompany an apparently
  incomplete text. No removal or repair of such outputs in the primary study.
- Small nonrandom qualitative sample with no independent human assessment.

## 9. Implications for RQ1/RQ2

The new defensible statement is restricted: in both existing models' tested
zero-shot settings, removing this explicit block yielded no statistically
detectable SARI change in any of 12 comparisons. This extends the Llama-only
finding to the second existing model, without establishing equivalence,
invariance, ISO adherence or the full causal effect of ISO. The effects are
not shown equal across models; no interaction test was performed. The study
does not answer questions about demonstration selection or one/few-shot runs.
Align this wording with the manuscript's exact RQ definitions before insertion;
their literal wording was not available in the inspected manuscript files.

## 10. Reviewer response and artifact status

See [the updated English draft](REVIEWER2_CONCERN1_DRAFT.md). It is grounded in
these completed artifacts; manuscript insertion and real section/table numbers
remain pending. Other reviewer concerns are not claimed resolved. Original
prompts, inference outputs, saved scores and prior Llama analysis files are
preserved. No commit, push, release, tag move or external message was made.
"""
    (DEST/"SCIENTIFIC_REPORT.md").write_text(report,encoding="utf-8")
    response="""# Updated draft response — Reviewer #2, Concern #1

Author-review draft. Results and artifacts are complete; manuscript integration
and final section/table references remain pending.

Thank you for highlighting the confounding between the baseline and ISO-based
prompts. We agree that their original comparison does not isolate the complete
causal effect of ISO 24495-1. We selected your proposed focused ablation of the
organization/summary block, rather than a length-matched non-ISO control.

We deleted only the section requesting information hierarchy, an initial
summary and logical grouping/chronological ordering. The ISO framing,
linguistic instructions, omission permissions, illustrative examples,
visual-format instructions and response restrictions were retained. Thus,
the intervention does not remove all structural guidance or equalize length.

We conducted 12 new zero-shot configurations across both models already used
in the paper, Llama 3.1 8B and Mixtral 8x7B, using the same ordered Cochrane
(125), PLABA (148) and TSAR2025 (100) inputs and original decoding parameters,
including the 512-token cap. All 1,492 outputs were retained. Evaluation
preserved the six original metric implementations and added explicitly defined
output length, compression and lexical copy rate. Recomputed original scores
matched all 108 stored aggregate metric values at reported precision.

For Llama ISO, SARI changes (ablated−original) were +0.047, +0.075 and +0.254
on Cochrane, PLABA and TSAR; the corresponding 95% paired bootstrap intervals
were [−0.484, 0.573], [−0.512, 0.654] and [−0.573, 1.092]. Llama ISO+examples
changes were −0.032, −0.102 and −0.110, with intervals [−0.444, 0.392],
[−0.602, 0.412] and [−0.877, 0.623].

For Mixtral ISO, changes were +0.089, +0.274 and +0.227, with intervals
[−0.621, 0.851], [−0.736, 1.298] and [−0.974, 1.401]. Mixtral ISO+examples
changes were −0.022, +0.139 and +0.769, with intervals [−0.897, 0.828],
[−0.885, 1.131] and [−0.294, 1.831].

Intervals used 10,000 paired item resamples. Two-sided within-item randomization
tests with 19,999 permutations found no significant contrasts at 0.05, even
before correction. We report Holm correction within each six-test model family
and an additional correction across all 12 contrasts. We do not interpret
non-significance as equivalence or claim an absence of structural effects.

An exploratory AI-assisted inspection used the same five prespecified source
positions per dataset for both prompt families and models (60 paired output
comparisons over 15 sources). It found heterogeneous structural changes,
preserved source/chronological order and lists that persisted or appeared after
ablation. This was not a validated human evaluation or an ISO-compliance rate.
In Mixtral, apparent incomplete outputs also occurred with stop termination,
so linguistic completeness cannot be inferred from termination metadata alone.

We report generation-cap terminations and retain all outputs. In Cochrane,
Llama ISO changes from 0 to 1 and ISO+examples from 5 to 7 out of 125;
Mixtral ISO changes from 7 to 17 and ISO+examples from 29 to 30 out of 125.
In PLABA, Mixtral ISO changes from 0 to 1 and ISO+examples remains 7/148.
All TSAR cells have no length terminations. Differential
termination and apparently incomplete stop outputs limit interpretation.
Historical model/runtime identity cannot be certified from older logs, and
PLABA row-based resampling does not account for possible document clustering.

The conclusion is limited to this block under the tested two-model zero-shot
conditions: no statistically detectable SARI change was observed. Prompt
length, instruction count, omission permissions and retained structural cues
remain potential confounds. The study therefore does not identify the full
effect of ISO 24495-1 or establish compliance, equivalence or effects in other
prompting settings. These qualifications should accompany the RQ1/RQ2 findings.

## Proposed manuscript insertion (not yet inserted)

“We conducted a focused organization/summary ablation in both existing models,
Llama 3.1 8B and Mixtral 8x7B, across the three datasets under zero-shot
prompting. Removing only the explicit hierarchy, initial-summary and logical-
grouping block produced SARI changes from −0.110 to +0.769 points; all 12
paired 95% intervals included zero and no paired randomization test rejected
at 0.05. This does not establish equivalence or ISO compliance. The results
concern reference-based SARI in these settings, while prompt length,
instruction count, omission permissions, retained formatting requirements and
termination behavior remain limitations.”

Before submission, integrate the full tables/methods/limitations and actual
section references. Do not claim that the paper has already been updated,
that all 72 configurations were ablated, or that a human study was conducted.
"""
    (DEST/"REVIEWER2_CONCERN1_DRAFT.md").write_text(response,encoding="utf-8")
    (DEST/"complete.json").write_text(json.dumps({"models":2,"ablation_configurations":12,
        "aggregate_evaluation_cells":30,"matched_original_metrics_reproduced":108,
        "paired_rows":1492,"statistical_comparisons":12,"qualitative_pairs":60,
        "unique_qualitative_source_rows":15,"all_CIs_include_zero":bool(((stats.ci95_low<0)&(stats.ci95_high>0)).all()),
        "all_raw_p_above_005":bool((stats.p_two_sided>0.05).all()),
        "manuscript_integration":"pending author review"},indent=2),encoding="utf-8")
    print("PASS: 12 statistical comparisons, 30 metric rows, 1492 paired rows, 108 original score checks.")


if __name__=="__main__":
    main()
