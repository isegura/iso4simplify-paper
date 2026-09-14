from __future__ import annotations

from functools import lru_cache
from typing import Dict

import evaluate
import numpy as np
import sacrebleu
import textstat
from bert_score import BERTScorer


def sari_score(orig_sents, sys_sents, refs_sents) -> float:
    """Legacy project SARI implementation.

    This is kept for reproducibility with previous project scores. For
    multi-reference datasets, prefer compute_sari_standard().
    """
    def get_ngrams(sentence, n):
        tokens = str(sentence).split()
        return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]

    def f1(tp, denom_p, denom_r):
        p = tp / denom_p if denom_p else 0.0
        r = tp / denom_r if denom_r else 0.0
        return (2 * p * r / (p + r)) if (p + r) else 0.0

    total = 0.0
    for orig, sys, ref in zip(orig_sents, sys_sents, refs_sents):
        add, keep, dele = [], [], []
        for n in range(1, 5):
            o = set(get_ngrams(orig, n))
            s = set(get_ngrams(sys, n))
            r = set(get_ngrams(ref, n))

            s_add = s - o
            r_add = r - o
            tp = len(s_add & r_add)
            add.append(f1(tp, len(s_add), len(r_add)))

            s_keep = s & o
            r_keep = r & o
            tp = len(s_keep & r_keep)
            keep.append(f1(tp, len(s_keep), len(r_keep)))

            s_del = o - s
            r_del = o - r
            tp = len(s_del & r_del)
            dele.append(f1(tp, len(s_del), len(r_del)))

        total += (np.mean(add) + np.mean(keep) + np.mean(dele)) / 3.0

    return (total / len(orig_sents)) * 100.0 if orig_sents else 0.0


def normalize_references_for_sari(references):
    if not references:
        return []

    first = references[0]
    if isinstance(first, (list, tuple)):
        return [[str(ref) for ref in refs] for refs in references]

    return [[str(ref)] for ref in references]


@lru_cache(maxsize=1)
def get_sari_metric():
    return evaluate.load("sari")


def compute_sari_standard(sources, predictions, references) -> float:
    metric = get_sari_metric()
    result = metric.compute(
        sources=[str(s) for s in sources],
        predictions=[str(p) for p in predictions],
        references=normalize_references_for_sari(references),
    )
    return round(float(result["sari"]), 2)


def compute_sari(
    sources,
    predictions,
    references,
    method: str = "legacy",
    fallback_to_legacy: bool = True,
) -> float:
    if method == "legacy":
        return round(float(sari_score(sources, predictions, references)), 2)

    if method == "standard":
        return compute_sari_standard(sources, predictions, references)

    if method == "auto":
        try:
            return compute_sari_standard(sources, predictions, references)
        except Exception as exc:
            if not fallback_to_legacy:
                raise
            print(f"Standard SARI unavailable; falling back to legacy SARI. Error: {exc}")
            return round(float(sari_score(sources, predictions, references)), 2)

    raise ValueError("Unknown SARI method. Use 'legacy', 'standard', or 'auto'.")


def compute_readability_metrics(predictions) -> Dict[str, float]:

    metrics = {
        "FKGL": textstat.flesch_kincaid_grade,
        "FRE": textstat.flesch_reading_ease,
    }

    return {
        name: round(float(np.nanmean([func(t) for t in predictions])), 2)
        for name, func in metrics.items()
    }


def compute_bertscore(predictions, references, lang: str = "en", return_mean: bool = True) -> Dict[str, float]:
    valid_items = []
    for idx, (prediction, reference) in enumerate(zip(predictions, references)):
        prediction_text = str(prediction).strip()
        if isinstance(reference, (list, tuple)):
            reference_is_empty = not any(str(ref).strip() for ref in reference)
        else:
            reference_is_empty = not str(reference).strip()

        if prediction_text and not reference_is_empty:
            valid_items.append((idx, prediction, reference))

    n_items = len(predictions)
    if not valid_items:
        if return_mean:
            return {
                "BERTScore-P": 0.0,
                "BERTScore-R": 0.0,
                "BERTScore-F1": 0.0,
            }

        return {
            "BERTScore-P": [0.0] * n_items,
            "BERTScore-R": [0.0] * n_items,
            "BERTScore-F1": [0.0] * n_items,
        }

    model_type = "xlm-roberta-large"
    if lang == 'en':
        model_type = 'roberta-large'
    scorer = BERTScorer(model_type=model_type, lang=lang, rescale_with_baseline=False) # Argumentos de configuración
    valid_predictions = [item[1] for item in valid_items]
    valid_references = [item[2] for item in valid_items]
    p, r, f1  = scorer.score(cands=valid_predictions, refs=valid_references)

    prefix = "BERTScore"
    if return_mean:
        return {
            f"{prefix}-P": round(float(p.sum() / n_items), 4),
            f"{prefix}-R": round(float(r.sum() / n_items), 4),
            f"{prefix}-F1": round(float(f1.sum() / n_items), 4),
        }

    p_scores = [0.0] * n_items
    r_scores = [0.0] * n_items
    f1_scores = [0.0] * n_items
    for pos, (idx, _, _) in enumerate(valid_items):
        p_scores[idx] = round(float(p[pos]), 4)
        r_scores[idx] = round(float(r[pos]), 4)
        f1_scores[idx] = round(float(f1[pos]), 4)

    return {
        f"{prefix}-P": p_scores,
        f"{prefix}-R": r_scores,
        f"{prefix}-F1": f1_scores,
    }

@lru_cache(maxsize=1)
def get_meaningbert_metric():
    return evaluate.load("davebulaval/meaningbert")

def compute_meaningbert(predictions, references, return_mean: bool = True) -> float:
    metric = get_meaningbert_metric()
    valid_items = []
    for idx, (prediction, reference) in enumerate(zip(predictions, references)):
        if str(prediction).strip() and str(reference).strip():
            valid_items.append((idx, prediction, reference))

    n_items = len(predictions)
    if not valid_items:
        return 0.0 if return_mean else [0.0] * n_items

    result = metric.compute(
        references=[item[2] for item in valid_items],
        predictions=[item[1] for item in valid_items],
    )
    # print(f"MeaningBERT raw result: {result}")
    valid_scores = [round(float(x), 2) for x in result["scores"]]

    if return_mean:
        return round(float(sum(valid_scores) / n_items), 2)

    scores = [0.0] * n_items
    for pos, (idx, _, _) in enumerate(valid_items):
        scores[idx] = valid_scores[pos]
    return scores
def evaluate_predictions(
    predictions,
    sources,
    references,
    references_multi_bleu,
    lang,
    eval_semantic,
    sari_method: str = "legacy",
) -> dict[str, float]:
    print("Evaluating predictions...", eval_semantic)
    scores={}
    # BLEU
    if references_multi_bleu is None:
        bleu = sacrebleu.corpus_bleu(predictions, [references]).score
    else:
        bleu = sacrebleu.corpus_bleu(predictions, references_multi_bleu).score
    scores["BLEU"] = round(bleu, 2)
    # SARI
    scores["SARI"] = compute_sari(
        sources=sources,
        predictions=predictions,
        references=references,
        method=sari_method,
    )
    readability_metrics = compute_readability_metrics(predictions)
    scores.update(readability_metrics)
    if eval_semantic:
        bertscore = compute_bertscore(predictions, references, lang=lang)
        scores["BERTScore-F1"] = bertscore["BERTScore-F1"]
        print(f"BERTScore-F1: {scores['BERTScore-F1']}")
        meaningbert = compute_meaningbert(predictions, sources)
        scores["MeaningBERT"] = meaningbert
        print(f"MeaningBERT: {meaningbert}")
    return scores

