"""Six historical metrics for completed selection-seed jobs; never generate text.

Default is validation only. --execute evaluates saved outputs offline.
Seed 42 reuses the historical per-item metric columns; BLEU is corpus BLEU.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
DEST = HERE / 'evaluation/metrics'
METRICS = ['SARI', 'BLEU', 'BERTScore-F1', 'MeaningBERT', 'FKGL', 'FRE']
ITEM_METRICS = [m for m in METRICS if m != 'BLEU']
KEYS = ['model', 'dataset', 'prompt', 'strategy']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def selected_jobs(seed, model=None, dataset=None):
    manifest = json.loads((HERE / 'experiment_manifest.json').read_text(encoding='utf-8'))
    return [j for j in manifest['jobs'] if j['selection_seed'] == (44 if seed == 42 else seed)
            and (model is None or j['model'] == model)
            and (dataset is None or j['dataset'] == dataset)]


def load_job(job, seed):
    manifest = json.loads((HERE / 'experiment_manifest.json').read_text(encoding='utf-8'))
    path = ROOT / job['historical_prediction_path' if seed == 42 else 'prediction_path']
    test_path = ROOT / job['test_path']
    # Reject active jobs BEFORE opening their CSV.
    if seed != 42:
        marker = HERE / 'logs' / job['model'] / f'seed_{seed}' / (job['job_id'] + '.complete.json')
        if not marker.exists():
            raise ValueError(f'Generation not certified complete: {marker}')
        proof = json.loads(marker.read_text(encoding='utf-8'))
        if proof['status'] != 'complete' or proof['rows'] != job['n'] or proof['prediction_sha256'] != sha(path):
            raise ValueError(f'Completion certificate mismatch: {path}')
    else:
        if sha(path) != manifest['source_sha256'][job['historical_prediction_path']]:
            raise ValueError(f'Historical predictions changed: {path}')
    if sha(test_path) != manifest['source_sha256'][job['test_path']]:
        raise ValueError(f'Test inputs changed: {test_path}')
    hashes = {str(p.relative_to(ROOT).as_posix()): sha(p) for p in (path, test_path)}
    frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
    test = pd.read_csv(test_path, keep_default_na=False, dtype={'text_id': str})
    if len(frame) != job['n'] or not frame[['text_id', 'original', 'reference']].equals(test[['text_id', 'original', 'reference']]):
        raise ValueError(f'Prediction/test row alignment failed: {path}')
    refs = [[str(r)] for r in frame.reference]
    if job['dataset'] == 'tsar2025':
        gold_path = ROOT / 'data/tsar2025/tsar2025_test_200.csv'
        hashes[gold_path.relative_to(ROOT).as_posix()] = sha(gold_path)
        gold = pd.read_csv(gold_path, keep_default_na=False, dtype={'text_id': str})
        gold['base_id'] = gold.text_id.str.extract(r'^(\d+)')
        refs = []
        for row in frame.itertuples():
            group = gold[gold.base_id == row.text_id]
            if len(group) != 2 or set(group.original) != {row.original}:
                raise ValueError(f'TSAR references/source mismatch: {row.text_id}')
            refs.append(group.reference.astype(str).tolist())
    if seed == 42:
        values = frame[ITEM_METRICS].apply(pd.to_numeric, errors='raise')
        if not np.isfinite(values.to_numpy()).all():
            raise ValueError('Nonfinite historical item scores')
    return frame, refs, hashes


def aggregate(items, predictions, refs):
    from sacrebleu.metrics import BLEU
    bleu = BLEU()
    score = bleu.corpus_score(predictions, list(map(list, zip(*refs)))).score
    return {**{m: float(items[m].mean()) for m in ITEM_METRICS}, 'BLEU': float(score)}, str(bleu.get_signature())


def compute_items(frame, refs):
    from eval_utils import get_sari_metric, compute_bertscore, compute_meaningbert
    import textstat
    predictions = frame.prediction.astype(str).tolist()
    sources = frame.original.astype(str).tolist()
    sari = get_sari_metric()
    result = pd.DataFrame({
        'SARI': [round(float(sari.compute(sources=[s], predictions=[p], references=[r])['sari']), 2)
                 for s, p, r in zip(sources, predictions, refs)],
        'FKGL': [round(float(textstat.flesch_kincaid_grade(p)), 2) for p in predictions],
        'FRE': [round(float(textstat.flesch_reading_ease(p)), 2) for p in predictions],
    })
    result['BERTScore-F1'] = compute_bertscore(predictions, refs, lang='en', return_mean=False)['BERTScore-F1']
    result['MeaningBERT'] = compute_meaningbert(predictions, sources, return_mean=False)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError('Nonfinite computed metric scores')
    return result


def evaluate(seed, model, dataset, execute=False):
    jobs = selected_jobs(seed, model, dataset)
    # Preflight every requested configuration before creating evaluation artifacts.
    for job in jobs:
        load_job(job, seed)
    print(f'Validated {len(jobs)} complete configurations, seed {seed}. No Ollama calls.', flush=True)
    if not execute:
        return
    os.chdir(ROOT)
    if seed != 42:
        from focused_metric_runtime import configure, MODULE
        configure()
        check = json.loads((ROOT / 'experiments/focused_ablation/meaningbert_validation/verification.json').read_text())
        if not check['all_match'] or check['meaningbert_module_sha256'] != sha(MODULE):
            raise ValueError('Historical MeaningBERT validation has not passed')
    versions = {name: importlib.metadata.version(name) for name in
                ['numpy', 'pandas', 'sacrebleu', 'evaluate', 'bert-score', 'textstat', 'transformers', 'torch']}
    code_files = [Path(__file__), ROOT / 'eval_utils.py', ROOT / 'focused_metric_runtime.py',
                  ROOT / 'experiments/focused_ablation/metric_sources/provenance.json',
                  ROOT / 'experiments/focused_ablation/metric_sources/meaningbert_original/meaningbert_original.py']
    for job in jobs:
        frame, refs, hashes = load_job(job, seed)
        folder = DEST / job['model'] / f'seed_{seed}'
        stem = f"{job['dataset']}_{job['prompt']}_{job['strategy']}"
        checkpoint = folder / (stem + '.json')
        item_path = folder / (stem + '_items.csv')
        fingerprint = dict(inputs=hashes, code={p.relative_to(ROOT).as_posix(): sha(p) for p in code_files}, versions=versions)
        if checkpoint.exists():
            previous = json.loads(checkpoint.read_text(encoding='utf-8'))
            if previous['fingerprint'] != fingerprint or previous['items_sha256'] != sha(item_path):
                raise ValueError(f'Evaluation checkpoint changed; inspect instead of overwriting: {checkpoint}')
            print(f'REUSE {stem}', flush=True)
            continue
        print(f'START {job["model"]} seed {seed} {stem}', flush=True)
        start = time.perf_counter()
        items = frame[ITEM_METRICS].astype(float).copy() if seed == 42 else compute_items(frame, refs)
        scores, signature = aggregate(items, frame.prediction.tolist(), refs)
        record = dict(**{k: job[k] for k in KEYS}, selection_seed=seed, n=len(frame), **scores,
                      empty_n=int(frame.prediction.str.strip().eq('').sum()),
                      capped_n=int(frame.done_reason.eq('length').sum()))
        items.insert(0, 'text_id', frame.text_id)
        items.insert(0, 'row_index', range(len(frame)))
        items['references_json'] = [json.dumps(r, ensure_ascii=False) for r in refs]
        for key in KEYS:
            items[key] = job[key]
        items['selection_seed'] = seed
        for path, digest in hashes.items():
            if sha(ROOT / path) != digest:
                raise ValueError(f'Input changed during evaluation: {path}')
        folder.mkdir(parents=True, exist_ok=True)
        items.to_csv(item_path, index=False)
        save_json(checkpoint, dict(status='complete', record=record, fingerprint=fingerprint,
            items_sha256=sha(item_path), bleu_signature=signature, elapsed_seconds=time.perf_counter()-start,
            historical_items_reused=seed == 42, predictions_verified_unchanged=True,
            methodology='Historical rounded item scores averaged without further rounding; corpus BLEU; all rows retained; TSAR A2/B1 jointly; MeaningBERT versus source; BERTScore scale 0--1.'))
        print(f'DONE {stem}', flush=True)
    records = []
    for job in jobs:
        path = DEST / job['model'] / f'seed_{seed}' / f"{job['dataset']}_{job['prompt']}_{job['strategy']}.json"
        records.append(json.loads(path.read_text(encoding='utf-8'))['record'])
    folder = DEST / 'summaries'
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(folder / f'{model or "all_models"}_{dataset or "all_datasets"}_seed_{seed}.csv', index=False)


def summarize(model=None, dataset=None):
    records = []
    for seed in (42, 44, 46):
        for job in selected_jobs(seed, model, dataset):
            folder = DEST / job['model'] / f'seed_{seed}'
            stem = f"{job['dataset']}_{job['prompt']}_{job['strategy']}"
            path = folder / (stem + '.json')
            if not path.exists():
                raise ValueError(f'All three evaluated seeds required; missing: {path}')
            saved = json.loads(path.read_text(encoding='utf-8'))
            if saved['status'] != 'complete' or saved['items_sha256'] != sha(folder / (stem + '_items.csv')):
                raise ValueError(f'Invalid evaluation artifact: {path}')
            for name, digest in saved['fingerprint']['inputs'].items():
                if sha(ROOT / name) != digest:
                    raise ValueError(f'Evaluation input changed: {name}')
            records.append(saved['record'])
    raw = pd.DataFrame(records)
    summaries = []
    for key, group in raw.groupby(KEYS, sort=True):
        if set(group.selection_seed) != {42, 44, 46} or len(group) != 3 or group.n.nunique() != 1:
            raise ValueError('Seed group incomplete or mismatched')
        for metric in METRICS:
            values = group.set_index('selection_seed')[metric]
            summaries.append(dict(zip(KEYS, key), metric=metric, n_seeds=3, n_test=int(group.n.iloc[0]),
                seed_42=float(values[42]), seed_44=float(values[44]), seed_46=float(values[46]),
                mean=float(values.mean()), sd=float(values.std(ddof=1)),
                minimum=float(values.min()), maximum=float(values.max())))
    folder = DEST / 'summaries'
    folder.mkdir(parents=True, exist_ok=True)
    label = f'{model or "all_models"}_{dataset or "all_datasets"}'
    raw.to_csv(folder / (label + '_per_seed.csv'), index=False)
    pd.DataFrame(summaries).to_csv(folder / (label + '_mean_sd.csv'), index=False)
    save_json(folder / (label + '_methodology.json'), dict(seeds=[42,44,46], sd_ddof=1,
        configurations=len(raw), corpus_bleu_not_sentence_mean=True, generation_calls=0,
        interpretation='Descriptive spread across three constrained demonstration selections; no equivalence or inferential test.'))
    print(f'Summarized {len(raw)} configurations; three seeds per condition.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, choices=[42, 44, 46])
    parser.add_argument('--model', choices=['llama', 'mixtral'])
    parser.add_argument('--dataset', choices=['cochrane', 'plaba', 'tsar2025'])
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--summarize', action='store_true')
    args = parser.parse_args()
    if args.summarize:
        if args.seed is not None or args.execute:
            parser.error('--summarize cannot be combined with --seed or --execute')
        summarize(args.model, args.dataset)
    else:
        if args.seed is None:
            parser.error('--seed is required for validation/evaluation')
        evaluate(args.seed, args.model, args.dataset, args.execute)
