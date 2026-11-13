"""Unified main-study SARI analysis. --prepare freezes metadata; --execute fits.

No inference, model download, semantic scoring or editing of historical outputs.
"""
import argparse
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import f as f_distribution

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'experiments/reviewer2_concern2'))
import run_statistics as historical
from statistics_core import fit_clustered, test_contrasts, adjust_by_family, cluster_bootstrap

PLAN = HERE / 'design'
OUT = HERE / 'results'
RETRIEVAL = ROOT / 'experiments/reviewer2_concern5/prepared_retrieval_20261102'
LEVELS = dict(dataset=['cochrane', 'plaba', 'tsar2025'], model=['llama', 'mixtral'],
              prompt=['minimal', 'iso', 'iso_examples'],
              condition=['zero', 'one', 'few_random', 'few_metric', 'few_retrieval'])
SPECS = [
    ('iso_minus_baseline', {'prompt': 'iso'}, {'prompt': 'minimal'}),
    ('iso_examples_minus_baseline', {'prompt': 'iso_examples'}, {'prompt': 'minimal'}),
    ('iso_examples_minus_iso', {'prompt': 'iso_examples'}, {'prompt': 'iso'}),
    ('one_minus_zero', {'condition': 'one'}, {'condition': 'zero'}),
    ('few_random_minus_one', {'condition': 'few_random'}, {'condition': 'one'}),
    ('few_metric_minus_few_random', {'condition': 'few_metric'}, {'condition': 'few_random'}),
    ('few_retrieval_minus_few_random', {'condition': 'few_retrieval'}, {'condition': 'few_random'}),
    ('few_retrieval_minus_few_metric', {'condition': 'few_retrieval'}, {'condition': 'few_metric'}),
    ('mixtral_minus_llama', {'model': 'mixtral'}, {'model': 'llama'}),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configurations():
    records = []
    for values in itertools.product(*LEVELS.values()):
        cell = dict(zip(LEVELS, values))
        for seed in ([42, 44, 46] if cell['condition'] in ['one', 'few_random'] else [0]):
            records.append(dict(**cell, selection_seed=seed,
                                cell_id='/'.join(values) + '/' + (str(seed) if seed else 'fixed')))
    return pd.DataFrame(records)


def margin(cells, filters):
    mask = np.ones(len(cells), dtype=bool)
    for key, value in filters.items():
        mask &= cells[key].eq(value).to_numpy()
    selected = cells[mask]
    counts = selected.groupby(list(LEVELS)).selection_seed.transform('size').to_numpy()
    w = np.zeros(len(cells))
    w[mask] = 1 / counts
    return w / w.sum()


def scalar_contrasts(cells):
    records, weights = [], []
    for name, plus, minus in SPECS:
        records.append(dict(family='global_9', contrast_id=name, model='all', dataset='all'))
        weights.append(margin(cells, plus) - margin(cells, minus))
    for model, dataset in itertools.product(LEVELS['model'], LEVELS['dataset']):
        for name, plus, minus in SPECS[:8]:
            context = dict(model=model, dataset=dataset)
            records.append(dict(family='local_48', contrast_id=f'{name}/{model}/{dataset}', model=model, dataset=dataset))
            weights.append(margin(cells, {**plus, **context}) - margin(cells, {**minus, **context}))
    return pd.DataFrame(records), np.array(weights)


def omnibus_restrictions(cells):
    nested = cells.groupby(list(LEVELS)).selection_seed.transform('size').to_numpy()
    result = []
    keys = list(LEVELS)
    for order in range(1, 5):
        for subset in itertools.combinations(keys, order):
            matrix = []
            for choices in itertools.product(*(LEVELS[key][1:] for key in subset)):
                choice = dict(zip(subset, choices))
                w = 1 / nested
                for key, levels in LEVELS.items():
                    if key in subset:
                        w = w * (cells[key].eq(choice[key]).astype(float).to_numpy() - cells[key].eq(levels[0]).astype(float).to_numpy())
                    else:
                        w = w / len(levels)
                matrix.append(w)
            result.append(('*'.join(subset), np.array(matrix)))
    return result


def omnibus_test(means, covariance, restrictions, df):
    q = restrictions @ means
    v = restrictions @ covariance @ restrictions.T
    rank = np.linalg.matrix_rank(restrictions)
    if rank != len(q) or np.linalg.matrix_rank(v) != rank:
        raise ValueError('Singular omnibus hypothesis; inspect, do not change test')
    f = float(q @ np.linalg.solve(v, q) / rank)
    return dict(F=f, df_num=rank, df_denom=df, p=float(f_distribution.sf(f, rank, df)))


def prepare():
    if PLAN.exists():
        validate_design()
        print('Frozen unified design verified; no outcomes read.')
        return
    cells = configurations()
    contrasts, weights = scalar_contrasts(cells)
    omnibus = omnibus_restrictions(cells)
    assert len(cells) == 162 and len(contrasts) == 57 and len(omnibus) == 15
    assert cells.cell_id.is_unique and np.linalg.matrix_rank(np.eye(162)) == 162
    assert np.allclose(weights.sum(axis=1), 0)
    sources = []
    hashes = {}
    for dataset in LEVELS['dataset']:
        path = ROOT / f'data/{dataset}/{dataset}_test.csv'
        hashes[path.relative_to(ROOT).as_posix()] = sha(path)
        test = pd.read_csv(path, keep_default_na=False, dtype={'text_id': str})
        for index, row in test.iterrows():
            sources.append(dict(dataset=dataset, row_index=index, text_id=row.text_id,
                                cluster_id=dataset + '/' + row.text_id, source_sha256=hashlib.sha256(row.original.encode()).hexdigest()))
    source = pd.DataFrame(sources)
    PLAN.mkdir()
    cells.to_csv(PLAN / 'cells.csv', index=False)
    contrasts.to_csv(PLAN / 'contrasts.csv', index=False)
    source.to_csv(PLAN / 'sources.csv', index=False)
    np.save(PLAN / 'contrast_weights.npy', weights)
    np.savez_compressed(PLAN / 'omnibus_restrictions.npz', **{name: r for name, r in omnibus})
    code = [Path(__file__), HERE / 'ANALYSIS_PLAN.md', ROOT / 'experiments/reviewer2_concern2/statistics_core.py']
    proof = dict(status='frozen_before_unified_fit_after_prior_outcome_inspection', cells=162, rows=20142,
                 source_groups=335, global_contrasts=9, local_contrasts=48, omnibus_terms=15,
                 bootstrap_draws=10000, bootstrap_seed=20261104, inference_calls=0,
                 provenance='Revision-stage extension; previous scores and analyses already known. Not preregistered.',
                 input_hashes=hashes,
                 code_hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in code},
                 design_hashes={p.name: sha(p) for p in PLAN.iterdir()})
    (PLAN / 'frozen.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('Frozen: 162 cells, 20,142 rows; 9 global + 48 local contrasts; 15 omnibus terms. No outcomes read.')


def validate_design():
    proof = json.loads((PLAN / 'frozen.json').read_text())
    for name, digest in {**proof['input_hashes'], **proof['code_hashes']}.items():
        assert sha(ROOT / name) == digest, name
    for name, digest in proof['design_hashes'].items():
        assert sha(PLAN / name) == digest, name
    cells = configurations()
    assert pd.read_csv(PLAN / 'cells.csv', keep_default_na=False).equals(cells)
    records, weights = scalar_contrasts(cells)
    np.testing.assert_array_equal(weights, np.load(PLAN / 'contrast_weights.npy'))
    return proof, cells, records, weights


def assemble(cells):
    old_cells, _, clusters, old_sums, old_counts, hashes = historical.assemble()
    old_complete = ROOT / 'experiments/reviewer2_concern2/statistics_results/joint_sari/complete.json'
    previous = json.loads(old_complete.read_text())
    for name, digest in {**previous['input_sha256'], **previous['code_sha256']}.items():
        assert sha(ROOT / name) == digest, name
        hashes[name] = digest
    hashes[old_complete.relative_to(ROOT).as_posix()] = sha(old_complete)
    sums = np.zeros((len(clusters), len(cells)))
    counts = np.zeros_like(sums)
    new_lookup = {row.cell_id: i for i, row in cells.iterrows()}
    for i, cell in old_cells.iterrows():
        target = new_lookup[cell.cell_id]
        sums[:, target] = old_sums[:, i]
        counts[:, target] = old_counts[:, i]
    lookup = {key: i for i, key in enumerate(clusters.cluster_id)}
    manifest = json.loads((RETRIEVAL / 'experiment_manifest.json').read_text())
    hashes[(RETRIEVAL / 'experiment_manifest.json').relative_to(ROOT).as_posix()] = sha(RETRIEVAL / 'experiment_manifest.json')
    retrieval_records = []
    for j in manifest['jobs']:
        prefix = f"{j['dataset']}_{j['prompt']}_few_retrieval"
        meta = RETRIEVAL / 'evaluation' / j['model'] / (prefix + '.json')
        item_path = meta.with_name(prefix + '_items.csv')
        saved = json.loads(meta.read_text())
        assert saved['status'] == 'complete' and sha(item_path) == saved['items_sha256']
        for name, digest in {**saved['fingerprint']['inputs'], **saved['fingerprint']['code']}.items():
            assert sha(ROOT / name) == digest, name
            hashes[name] = digest
        marker = RETRIEVAL / 'logs' / j['model'] / (j['job_id'] + '.complete.json')
        cert = json.loads(marker.read_text())
        assert cert == dict(status='complete', rows=j['n'], prediction_sha256=sha(ROOT / j['prediction_path']))
        frame = pd.read_csv(item_path, keep_default_na=False, dtype={'text_id': str})
        test = pd.read_csv(ROOT / j['test_path'], keep_default_na=False, dtype={'text_id': str})
        assert len(frame) == j['n'] and frame.text_id.tolist() == test.text_id.tolist()
        assert frame.row_index.tolist() == list(range(j['n']))
        seed42 = pd.read_csv(ROOT / f"experiments/reviewer2_concern2/evaluation/metrics/{j['model']}/seed_42/{j['dataset']}_{j['prompt']}_few_random_items.csv", keep_default_na=False, dtype={'text_id': str})
        assert [sorted(json.loads(r)) for r in frame.references_json] == [sorted(json.loads(r)) for r in seed42.references_json]
        target = new_lookup[f"{j['dataset']}/{j['model']}/{j['prompt']}/few_retrieval/fixed"]
        values = frame.SARI.to_numpy(float)
        assert np.isfinite(values).all() and np.isclose(values.mean(), saved['record']['SARI'])
        for tid, value in zip(frame.text_id, values):
            group = lookup[j['dataset'] + '/' + tid]
            sums[group, target] += value
            counts[group, target] += 1
        retrieval_records.append((target, saved['record']['SARI']))
        for path in [meta, item_path, marker]:
            hashes[path.relative_to(ROOT).as_posix()] = sha(path)
    assert counts.sum() == 20142 and len(clusters) == 335 and np.all(counts.sum(axis=0) > 0)
    means = sums.sum(axis=0) / counts.sum(axis=0)
    for target, value in retrieval_records:
        assert np.isclose(means[target], value, atol=1e-10)
    old_estimates = pd.read_csv(ROOT / 'experiments/reviewer2_concern2/statistics_results/joint_sari/cell_estimates.csv')
    for r in old_estimates.itertuples():
        assert np.isclose(means[new_lookup[r.cell_id]], r.SARI, atol=1e-10)
    return clusters, sums, counts, hashes


def execute():
    _, cells, records, weights = validate_design()
    if (OUT / 'complete.json').exists():
        proof = json.loads((OUT / 'complete.json').read_text())
        for name, digest in {**proof['input_hashes'], **proof['output_hashes'], **proof['code_hashes']}.items():
            assert sha(ROOT / name) == digest, name
        print('Completed unified analysis verified; no outputs replaced.')
        return
    if OUT.exists():
        raise FileExistsError('Partial results exist; inspect before rerunning')
    clusters, sums, counts, hashes = assemble(cells)
    means, covariance = fit_clustered(sums, counts)
    df = []
    for w in weights:
        datasets = cells.loc[w != 0, 'dataset'].unique()
        df.append(int(clusters.dataset.isin(datasets).sum()) - 1)
    scalar = records.copy()
    for key, values in test_contrasts(means, covariance, weights, df).items():
        scalar[key] = values
    scalar['df'] = df
    scalar['q_bh'] = adjust_by_family(scalar.p, scalar.family)
    scalar['reject_bh_005'] = scalar.q_bh < .05
    draws, ci = cluster_bootstrap(sums, counts, clusters.dataset.to_numpy(), weights, repetitions=10000, seed=20261104)
    scalar['bootstrap_ci_low'], scalar['bootstrap_ci_high'] = ci
    omnibus_rows = []
    for name, r in omnibus_restrictions(cells):
        omnibus_rows.append(dict(term=name, order=len(name.split('*')), **omnibus_test(means, covariance, r, len(clusters)-1)))
    omnibus = pd.DataFrame(omnibus_rows)
    omnibus['q_bh'] = adjust_by_family(omnibus.p, ['omnibus_15'] * len(omnibus))
    omnibus['reject_bh_005'] = omnibus.q_bh < .05
    estimates = cells.assign(n=counts.sum(axis=0).astype(int), SARI=means)
    structural = estimates.groupby(list(LEVELS), sort=False).SARI.mean().reset_index()
    for name, digest in hashes.items():
        assert sha(ROOT / name) == digest, name
    OUT.mkdir()
    estimates.to_csv(OUT / 'cell_estimates.csv', index=False)
    structural.to_csv(OUT / 'structural_means.csv', index=False)
    scalar.to_csv(OUT / 'all_scalar_contrasts.csv', index=False)
    scalar[scalar.family.eq('global_9')].to_csv(OUT / 'global_sari.csv', index=False)
    scalar[scalar.family.eq('local_48')].to_csv(OUT / 'local_sari.csv', index=False)
    omnibus.to_csv(OUT / 'omnibus_sari.csv', index=False)
    clusters.to_csv(OUT / 'clusters.csv', index=False)
    np.savez_compressed(OUT / 'sufficient_statistics.npz', sums=sums, counts=counts, covariance=covariance)
    np.save(OUT / 'bootstrap_contrasts.npy', draws)
    old = pd.read_csv(ROOT / 'experiments/reviewer2_concern2/statistics_results/joint_sari/primary_sari.csv')
    reconcile = old[['contrast_id', 'effect', 'q_bh']].merge(scalar[scalar.family.eq('global_9')][['contrast_id', 'effect', 'q_bh']], on='contrast_id', suffixes=('_old_four_strategies', '_new_five_strategies'))
    reconcile.to_csv(OUT / 'historical_global_reconciliation.csv', index=False)
    proof = dict(status='complete', configurations=162, structural_cells=90, response_instances=20142,
                 evaluation_rows=373, source_clusters=335, bootstrap_replicates=10000, bootstrap_seed=20261104,
                 families=dict(global_scalar=9, local_scalar=48, omnibus=15),
                 outcome_inspection_preceded_extension=True, externally_preregistered=False,
                 conditional_on_observed_selections=True, new_inference_calls=0, new_metric_evaluations=0,
                 input_hashes=hashes,
                 code_hashes=json.loads((PLAN / 'frozen.json').read_text())['code_hashes'],
                 output_hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in OUT.iterdir()},
                 versions={name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy']})
    (OUT / 'complete.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(scalar[scalar.family.eq('global_9')][['contrast_id', 'effect', 'bootstrap_ci_low', 'bootstrap_ci_high', 'q_bh']].to_string(index=False))
    print(omnibus[['term', 'F', 'df_num', 'q_bh']].to_string(index=False))
    print('Complete unified analysis:', OUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute()
    if not args.prepare and not args.execute:
        parser.error('Use --prepare (metadata only) or --execute (frozen design required)')
