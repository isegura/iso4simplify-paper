"""Finish original zero/few-metric descriptors; never opens seed-44/46 files."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = HERE/'evaluation/historical_fixed'
SEED_STUDY = ROOT/'experiments/reviewer2_concern2'
HELPER = SEED_STUDY/'evaluate_descriptors.py'
spec = importlib.util.spec_from_file_location('existing_descriptors', HELPER)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
MEASURES = ['LEN_COMPLEX', 'LEN_PRED', 'LEN_REF', 'compression_ratio', 'copy_rate']
SUMMARY_COLUMNS = ['model', 'dataset', 'prompt', 'strategy', 'selection_seed', 'n'] + ['mean_'+m for m in MEASURES] + ['empty_prediction_n', 'reached_generation_limit_n']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    if DEST.exists():
        raise FileExistsError(f'Completed/partial output exists; inspect rather than overwrite: {DEST}')
    audit_path = ROOT/'audits/original_paper_statistics_20261022/methodology.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    historical_hashes = {Path(name).as_posix(): digest for name, digest in audit['source_hashes'].items()}
    manifest_path = SEED_STUDY/'experiment_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    old_proof_path = SEED_STUDY/'evaluation/descriptors/summaries/all_models_all_datasets_seed_42.json'
    old_proof = json.loads(old_proof_path.read_text(encoding='utf-8'))
    old_summary_path = old_proof_path.with_suffix('.csv')
    if not old_proof['predictions_verified_unchanged'] or old_proof['descriptor_code_sha256'] != sha(HELPER):
        raise ValueError('Previous descriptor implementation/provenance changed')
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in [audit_path, manifest_path, old_proof_path, old_summary_path, HELPER]}
    # Verify the provenance of the 36 original one/few-random cells being reused.
    for name, digest in old_proof['input_sha256'].items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Historical descriptor inputs changed: {name}')
        hashes[name] = digest
    gold_path = ROOT/'data/tsar2025/tsar2025_test_200.csv'
    if sha(gold_path) != old_proof['input_sha256'][gold_path.relative_to(ROOT).as_posix()]:
        raise ValueError('TSAR gold changed')
    gold = pd.read_csv(gold_path, keep_default_na=False, dtype={'text_id': str})
    gold['base_id'] = gold.text_id.str.extract(r'^(\d+)')
    tests = {}
    for dataset, n in [('cochrane', 125), ('plaba', 148), ('tsar2025', 100)]:
        path = ROOT/'data'/dataset/f'{dataset}_test.csv'
        name = path.relative_to(ROOT).as_posix()
        if sha(path) != manifest['source_sha256'][name]:
            raise ValueError(f'Test set changed: {name}')
        tests[dataset] = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
        if len(tests[dataset]) != n:
            raise ValueError('Unexpected test size')
        hashes[name] = sha(path)
    # Retain all computed tables in memory until all 36 source files pass validation.
    summaries, tables = [], []
    for model, dataset, prompt, strategy in itertools.product(['llama', 'mixtral'], tests,
            ['minimal', 'iso', 'iso_examples'], ['zero', 'few_metric']):
        short = 'llama3_1_8b' if model == 'llama' else 'mixtral_latest'
        path = ROOT/'outputs'/f'{model}_512'/f'predictions_{short}_{dataset}_{prompt}_{strategy}.csv'
        name = path.relative_to(ROOT).as_posix()
        if sha(path) != historical_hashes[name]:
            raise ValueError(f'Original prediction changed: {name}')
        hashes[name] = sha(path)
        frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
        test = tests[dataset]
        if not frame[['text_id', 'original', 'reference']].equals(test[['text_id', 'original', 'reference']]):
            raise ValueError(f'Test/prediction alignment failed: {name}')
        records = []
        for i, row in frame.iterrows():
            refs = [row.reference]
            if dataset == 'tsar2025':
                group = gold[gold.base_id == row.text_id]
                if len(group) != 2 or set(group.original) != {row.original}:
                    raise ValueError(f'TSAR source/reference mismatch: {row.text_id}')
                refs = group.reference.tolist()
            values = helper.measures(row.original, row.prediction, refs)
            records.append(dict(model=model, dataset=dataset, prompt=prompt, strategy=strategy,
                selection_seed='', row_index=i, text_id=row.text_id, references_json=json.dumps(refs, ensure_ascii=False),
                done_reason=row.done_reason, **values,
                empty_prediction=not row.prediction.strip(), reached_generation_limit=row.done_reason == 'length'))
        items = pd.DataFrame(records)
        if not np.isfinite(items[MEASURES].to_numpy()).all() or not items.copy_rate.between(0,1).all():
            raise ValueError('Invalid descriptors')
        summary = dict(model=model, dataset=dataset, prompt=prompt, strategy=strategy, selection_seed='', n=len(items))
        summary.update({'mean_'+key: float(items[key].mean()) for key in MEASURES})
        summary.update(empty_prediction_n=int(items.empty_prediction.sum()), reached_generation_limit_n=int(items.reached_generation_limit.sum()))
        summaries.append(summary)
        tables.append((model, f'{dataset}_{prompt}_{strategy}_items.csv', items))
    fixed = pd.DataFrame(summaries)[SUMMARY_COLUMNS]
    old = pd.read_csv(old_summary_path, keep_default_na=False)[SUMMARY_COLUMNS]
    if len(old) != 36 or set(old.strategy) != {'one', 'few_random'} or not old.selection_seed.eq(42).all():
        raise ValueError('Unexpected original one/few-random descriptor summary')
    # Check each reused summary against its existing item table, not just its provenance sidecar.
    for row in old.to_dict('records'):
        path = SEED_STUDY/'evaluation/descriptors'/row['model']/'seed_42'/f"{row['dataset']}_{row['prompt']}_{row['strategy']}_items.csv"
        prior = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
        test = tests[row['dataset']]
        if len(prior) != len(test) or prior.text_id.tolist() != test.text_id.tolist() or prior.row_index.tolist() != list(range(len(test))):
            raise ValueError('Original descriptor item alignment failed')
        for key in MEASURES:
            if not np.isclose(prior[key].mean(), row['mean_'+key], atol=1e-12, rtol=0):
                raise ValueError('Original descriptor summary/item mismatch')
        for key in ['empty_prediction', 'reached_generation_limit']:
            if int(prior[key].sum()) != row[key+'_n']:
                raise ValueError('Original descriptor count mismatch')
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
    combined = pd.concat([old, fixed], ignore_index=True).sort_values(['model','dataset','prompt','strategy'])
    if len(combined) != 72 or int(combined.n.sum()) != 8952 or combined.duplicated(['model','dataset','prompt','strategy']).any():
        raise ValueError('Combined original scope mismatch')
    for name, digest in hashes.items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Input changed during evaluation: {name}')
    DEST.mkdir(parents=True, exist_ok=False)
    for model, filename, items in tables:
        folder = DEST/'items'/model
        folder.mkdir(parents=True, exist_ok=True)
        items.to_csv(folder/filename, index=False)
    fixed.to_csv(DEST/'fixed_36_summary.csv', index=False)
    combined.to_csv(DEST/'all_72_original_summary.csv', index=False)
    provenance = dict(status='complete', newly_computed_configurations=36, newly_computed_rows=int(fixed.n.sum()),
        reused_seed42_configurations=36, combined_original_configurations=72, combined_original_rows=int(combined.n.sum()),
        input_sha256=hashes, driver_sha256=sha(Path(__file__)), predictions_verified_unchanged=True,
        new_seed_files_read=False, ollama_calls=0, semantic_model_calls=0, statistical_tests_run=False,
        word_count='len(text.split())', compression='mean of per-row output/source word ratios',
        copy_rate='mean per-row fraction of output whitespace tokens in source token set; case and punctuation retained; empty output=0',
        tsar_references='A2/B1 jointly; LEN_REF mean of their word counts',
        plaba='all 148 original rows retained; no inferential independence assumption made here',
        selection_seed='blank for original fixed zero/few_metric; 42 for historical one/few_random; not generation seed',
        scope='historical original configurations only; no 44/46 seed analysis')
    (DEST/'complete.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in provenance.items() if key != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    evaluate()
