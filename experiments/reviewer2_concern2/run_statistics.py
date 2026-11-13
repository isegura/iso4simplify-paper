"""Concern 2: default checks readiness only; --execute runs the frozen SARI plan.

Never generates text, loads semantic models, edits predictions or writes LaTeX.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from prepare_statistics import configurations, build_contrasts
from statistics_core import fit_clustered, test_contrasts, adjust_by_family, cluster_bootstrap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN = HERE / 'statistics_plan'
METRICS = HERE / 'evaluation/metrics'
DEST = HERE / 'statistics_results/joint_sari'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric_paths(cell):
    folder = METRICS / cell['model'] / f"seed_{cell['selection_seed']}"
    stem = f"{cell['dataset']}_{cell['prompt']}_{cell['condition']}"
    return folder / (stem + '.json'), folder / (stem + '_items.csv')


def fixed_prediction_path(cell):
    short = 'llama3_1_8b' if cell['model'] == 'llama' else 'mixtral_latest'
    return ROOT / 'outputs' / (cell['model'] + '_512') / f"predictions_{short}_{cell['dataset']}_{cell['prompt']}_{cell['condition']}.csv"


def readiness(cells):
    """File inventory only: do not open new prediction or metric files."""
    missing = []
    complete_metric_cells = 0
    for cell in cells.to_dict('records'):
        if cell['selection_seed']:
            paths = metric_paths(cell)
            if all(p.is_file() for p in paths):
                complete_metric_cells += 1
            else:
                missing.extend(str(p.relative_to(ROOT)) for p in paths if not p.is_file())
        elif not fixed_prediction_path(cell).is_file():
            missing.append(str(fixed_prediction_path(cell).relative_to(ROOT)))
    return dict(ready_by_file_inventory=not missing, metric_cells_available=complete_metric_cells,
                metric_cells_required=108, historical_fixed_cells=36,
                missing_files=missing, outcome_files_opened=False, statistical_tests_run=False)


def validate_plan():
    report = json.loads((PLAN / 'validation.json').read_text(encoding='utf-8'))
    for path, key in [(HERE/'PLAN_ESTADISTICO.md', 'plan_sha256'),
                      (HERE/'prepare_statistics.py', 'code_sha256'),
                      (HERE/'statistics_core.py', 'statistics_core_sha256')]:
        if sha(path) != report[key]:
            raise ValueError(f'Frozen statistical specification changed: {path}')
    for name, digest in report['source_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'Test set changed: {name}')
    cells = configurations()
    stored = pd.read_csv(PLAN/'joint_model_cells.csv', keep_default_na=False)
    if not stored.equals(cells):
        raise ValueError('Stored cells differ from the statistical design')
    expected = build_contrasts(cells)
    stored_weights = pd.read_csv(PLAN/'contrast_weights.csv')
    for row in expected:
        found = stored_weights[stored_weights.contrast_id == row['contrast_id']]
        vector = found.set_index('cell_id').weight.reindex(cells.cell_id, fill_value=0).to_numpy()
        if set(found.family) != {row['family']} or not np.allclose(vector, row['weights'].to_numpy(), atol=1e-14, rtol=0):
            raise ValueError(f'Stored contrast weights changed: {row["contrast_id"]}')
    return cells, expected, report


def assemble():
    cells, contrasts, report = validate_plan()
    inventory = readiness(cells)
    if not inventory['ready_by_file_inventory']:
        raise ValueError(f"Complete all metric evaluations first: {len(inventory['missing_files'])} missing files")
    source_rows = []
    for dataset in cells.dataset.unique():
        test = pd.read_csv(ROOT/'data'/dataset/f'{dataset}_test.csv', keep_default_na=False, dtype={'text_id': str})
        for index, row in test.iterrows():
            source_rows.append(dict(dataset=dataset, row_index=index, text_id=row.text_id,
                                    cluster_id=dataset+'/'+row.text_id,
                                    source_sha256=hashlib.sha256(row.original.encode()).hexdigest()))
    sources = pd.DataFrame(source_rows)
    stored_sources = pd.read_csv(PLAN/'source_clusters.csv', keep_default_na=False, dtype={'text_id': str})
    if not sources.equals(stored_sources):
        raise ValueError('Document cluster definitions changed')
    clusters = sources[['cluster_id', 'dataset']].drop_duplicates().reset_index(drop=True)
    cluster_lookup = {name: i for i, name in enumerate(clusters.cluster_id)}
    sums = np.zeros((len(clusters), len(cells)))
    counts = np.zeros_like(sums)
    audit_path = ROOT/'audits/original_paper_statistics_20261022/methodology.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    historical_hashes = {Path(name).as_posix(): digest for name, digest in audit['source_hashes'].items()}
    hashes = {audit_path.relative_to(ROOT).as_posix(): sha(audit_path)}
    for cell_index, cell in enumerate(cells.to_dict('records')):
        expected_source = sources[sources.dataset == cell['dataset']].reset_index(drop=True)
        if cell['selection_seed']:
            metadata_path, items_path = metric_paths(cell)
            saved = json.loads(metadata_path.read_text(encoding='utf-8'))
            if saved['status'] != 'complete' or saved['items_sha256'] != sha(items_path):
                raise ValueError(f'Metric completion/hash mismatch: {metadata_path}')
            for name, digest in dict(saved['fingerprint']['inputs'], **saved['fingerprint']['code']).items():
                if sha(ROOT/name) != digest:
                    raise ValueError(f'Metric input/code changed: {name}')
                hashes[name] = digest
            for name in ['dataset', 'model', 'prompt', 'selection_seed']:
                if saved['record'][name] != cell[name]:
                    raise ValueError(f'Metric metadata mismatch: {name}')
            if saved['record']['strategy'] != cell['condition']:
                raise ValueError('Metric strategy mismatch')
            if cell['selection_seed'] in (44, 46):
                job_id = f"{cell['model']}_seed{cell['selection_seed']}_{cell['dataset']}_{cell['prompt']}_{cell['condition']}"
                marker = HERE/'logs'/cell['model']/f"seed_{cell['selection_seed']}"/(job_id+'.complete.json')
                proof = json.loads(marker.read_text(encoding='utf-8'))
                predicted = [name for name in saved['fingerprint']['inputs'] if '/predictions/' in name]
                if len(predicted) != 1 or proof['status'] != 'complete' or proof['rows'] != len(expected_source) or proof['prediction_sha256'] != sha(ROOT/predicted[0]):
                    raise ValueError('Generation completion proof mismatch')
                hashes[marker.relative_to(ROOT).as_posix()] = sha(marker)
            frame = pd.read_csv(items_path, keep_default_na=False, dtype={'text_id': str})
            if not frame[['row_index', 'text_id']].equals(expected_source[['row_index', 'text_id']]):
                raise ValueError(f'Metric row alignment mismatch: {items_path}')
            for name in ['dataset', 'model', 'prompt', 'selection_seed']:
                if not frame[name].eq(cell[name]).all():
                    raise ValueError(f'Metric item metadata mismatch: {name}')
            if not frame.strategy.eq(cell['condition']).all() or saved['record']['n'] != len(frame):
                raise ValueError('Metric item configuration mismatch')
            if not np.isclose(frame.SARI.astype(float).mean(), saved['record']['SARI'], atol=1e-10, rtol=0):
                raise ValueError('SARI item/aggregate mismatch')
            hashes[metadata_path.relative_to(ROOT).as_posix()] = sha(metadata_path)
            hashes[items_path.relative_to(ROOT).as_posix()] = sha(items_path)
        else:
            path = fixed_prediction_path(cell)
            name = path.relative_to(ROOT).as_posix()
            if sha(path) != historical_hashes[name]:
                raise ValueError(f'Historical fixed prediction changed: {path}')
            frame = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
            test = pd.read_csv(ROOT/'data'/cell['dataset']/f"{cell['dataset']}_test.csv", keep_default_na=False, dtype={'text_id': str})
            if not frame[['text_id', 'original', 'reference']].equals(test[['text_id', 'original', 'reference']]):
                raise ValueError(f'Historical row alignment mismatch: {path}')
            hashes[name] = sha(path)
        values = pd.to_numeric(frame.SARI, errors='raise').to_numpy(float)
        if len(values) != len(expected_source) or not np.isfinite(values).all():
            raise ValueError('Invalid SARI values or row counts')
        for source, score in zip(expected_source.itertuples(), values):
            index = cluster_lookup[source.cluster_id]
            sums[index, cell_index] += score
            counts[index, cell_index] += 1
    if int(counts.sum()) != report['rows'] or len(clusters) != report['source_clusters']:
        raise ValueError('Final dimensions differ from frozen design')
    return cells, contrasts, clusters, sums, counts, hashes


def analyze(cells, contrasts, clusters, sums, counts, repetitions=10000):
    means, covariance = fit_clustered(sums, counts)
    weights = np.vstack([r['weights'].to_numpy() for r in contrasts])
    dfs = []
    for r, vector in zip(contrasts, weights):
        datasets = cells.loc[vector != 0, 'dataset'].unique()
        dfs.append(int(clusters.dataset.isin(datasets).sum())-1)
    result = test_contrasts(means, covariance, weights, dfs)
    draws, intervals = cluster_bootstrap(sums, counts, clusters.dataset.to_numpy(), weights,
                                         repetitions=repetitions, seed=20261023)
    effects = pd.DataFrame({key: result[key] for key in result})
    effects.insert(0, 'contrast_id', [r['contrast_id'] for r in contrasts])
    effects.insert(0, 'family', [r['family'] for r in contrasts])
    effects['df'] = dfs
    effects['q_bh'] = adjust_by_family(effects.p, effects.family)
    effects['reject_bh_005'] = effects.q_bh < .05
    effects['bootstrap_ci_low'], effects['bootstrap_ci_high'] = intervals
    estimates = cells.copy()
    estimates['n'] = counts.sum(axis=0).astype(int)
    estimates['SARI'] = means
    return estimates, effects, covariance, draws


def main(execute=False):
    cells, _, _ = validate_plan()
    inventory = readiness(cells)
    if not execute:
        # Compact status rather than hundreds of paths; no outcome files opened.
        print(json.dumps({k: v for k, v in inventory.items() if k != 'missing_files'}, indent=2))
        print(f"Missing files: {len(inventory['missing_files'])}. No statistical analysis executed.")
        return
    if DEST.exists():
        raise FileExistsError(f'Refusing to replace statistical results: {DEST}')
    start = time.perf_counter()
    cells, contrasts, clusters, sums, counts, hashes = assemble()
    estimates, effects, covariance, draws = analyze(cells, contrasts, clusters, sums, counts)
    for name, digest in hashes.items():
        if sha(ROOT/name) != digest:
            raise ValueError(f'Input changed while running: {name}')
    DEST.mkdir(parents=True, exist_ok=False)
    estimates.to_csv(DEST/'cell_estimates.csv', index=False)
    effects.to_csv(DEST/'all_contrasts.csv', index=False)
    effects[effects.family == 'primary_7'].to_csv(DEST/'primary_sari.csv', index=False)
    effects[effects.family == 'secondary_36'].to_csv(DEST/'secondary_sari.csv', index=False)
    clusters.to_csv(DEST/'clusters.csv', index=False)
    np.savez_compressed(DEST/'sufficient_statistics.npz', sums=sums, counts=counts, covariance=covariance)
    np.save(DEST/'bootstrap_contrasts.npy', draws)
    code = {path.relative_to(ROOT).as_posix(): sha(path) for path in
            [Path(__file__), HERE/'statistics_core.py', HERE/'prepare_statistics.py', HERE/'PLAN_ESTADISTICO.md']}
    complete = dict(status='complete', configurations=144, rows=int(counts.sum()), clusters=len(clusters),
        bootstrap_replicates=10000, bootstrap_seed=20261023, input_sha256=hashes, code_sha256=code,
        elapsed_seconds=time.perf_counter()-start, ollama_calls=0, conditional_on_observed_selections=True,
        versions={name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy']})
    (DEST/'complete.json').write_text(json.dumps(complete, indent=2), encoding='utf-8')
    print(f'Complete: {DEST}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    main(parser.parse_args().execute)
