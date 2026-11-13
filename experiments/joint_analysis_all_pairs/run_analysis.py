"""Expand scalar hypotheses to every pair of strategies; preserve prior results."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / 'experiments/joint_analysis_final'
sys.path.insert(0, str(PREVIOUS))
import run_analysis as parent  # when run as __main__, imports the prior module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design(cells):
    specs = list(parent.SPECS[:3])
    strategies = parent.LEVELS['condition']
    for earlier, later in itertools.combinations(strategies, 2):
        specs.append((later + '_minus_' + earlier, {'condition': later}, {'condition': earlier}))
    specs.append(parent.SPECS[-1])
    records, weights = [], []
    for name, plus, minus in specs:
        records.append(dict(family='global_14', contrast_id=name, model='all', dataset='all'))
        weights.append(parent.margin(cells, plus) - parent.margin(cells, minus))
    for model, dataset in itertools.product(parent.LEVELS['model'], parent.LEVELS['dataset']):
        for name, plus, minus in specs[:-1]:
            context = dict(model=model, dataset=dataset)
            records.append(dict(family='local_78', contrast_id=f'{name}/{model}/{dataset}', **context))
            weights.append(parent.margin(cells, {**plus, **context}) - parent.margin(cells, {**minus, **context}))
    return pd.DataFrame(records), np.array(weights)


def verify_parent():
    proof = json.loads((PREVIOUS / 'results/complete.json').read_text())
    for path, digest in {**proof['input_hashes'], **proof['output_hashes'], **proof['code_hashes']}.items():
        assert sha(ROOT / path) == digest, path
    return proof


def prepare():
    folder = HERE / 'design'
    if folder.exists():
        validate()
        print('Expanded design already frozen; verified.')
        return
    cells = parent.configurations()
    records, weights = design(cells)
    assert records.groupby('family').size().to_dict() == {'global_14': 14, 'local_78': 78}
    assert records.contrast_id.is_unique
    np.testing.assert_allclose(weights.sum(axis=1), 0, atol=1e-15)
    assert len(set(records.iloc[3:13].contrast_id)) == 10
    folder.mkdir()
    records.to_csv(folder / 'contrasts.csv', index=False)
    np.save(folder / 'contrast_weights.npy', weights)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in [Path(__file__), HERE / 'ANALYSIS_PLAN.md', PREVIOUS / 'run_analysis.py', ROOT / 'experiments/reviewer2_concern2/statistics_core.py']}
    proof = dict(status='expanded_list_frozen_after_prior_outcomes_known', global_contrasts=14, local_contrasts=78, omnibus_tests=15,
                 bootstrap_replicates=10000, bootstrap_seed=20261104, code_plan_hashes=hashes,
                 design_hashes={p.name: sha(p) for p in folder.iterdir()})
    (folder / 'frozen.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('Frozen 14 global + 78 local contrasts, including all ten strategy pairs.')


def validate():
    proof = json.loads((HERE / 'design/frozen.json').read_text())
    for path, digest in proof['code_plan_hashes'].items():
        assert sha(ROOT / path) == digest, path
    for name, digest in proof['design_hashes'].items():
        assert sha(HERE / 'design' / name) == digest
    records, weights = design(parent.configurations())
    np.testing.assert_array_equal(weights, np.load(HERE / 'design/contrast_weights.npy'))
    return proof, records, weights


def execute():
    frozen, records, weights = validate()
    prior = verify_parent()
    out = HERE / 'results'
    if (out / 'complete.json').exists():
        saved = json.loads((out / 'complete.json').read_text())
        for path, digest in saved['output_hashes'].items():
            assert sha(ROOT / path) == digest
        print('Expanded results verified; nothing overwritten.')
        return
    if out.exists():
        raise FileExistsError('Partial expanded output: inspect before rerunning')
    cells = parent.configurations()
    sufficient = np.load(PREVIOUS / 'results/sufficient_statistics.npz')
    clusters = pd.read_csv(PREVIOUS / 'results/clusters.csv')
    sums, counts, covariance = sufficient['sums'], sufficient['counts'], sufficient['covariance']
    means = sums.sum(axis=0) / counts.sum(axis=0)
    df = []
    for w in weights:
        datasets = cells.loc[w != 0, 'dataset'].unique()
        df.append(int(clusters.dataset.isin(datasets).sum()) - 1)
    results = records.copy()
    for key, value in parent.test_contrasts(means, covariance, weights, df).items():
        results[key] = value
    results['df'] = df
    results['q_bh'] = parent.adjust_by_family(results.p, results.family)
    results['reject_bh_005'] = results.q_bh < .05
    draws, intervals = parent.cluster_bootstrap(sums, counts, clusters.dataset.to_numpy(), weights, repetitions=10000, seed=20261104)
    results['bootstrap_ci_low'], results['bootstrap_ci_high'] = intervals
    old = pd.read_csv(PREVIOUS / 'results/all_scalar_contrasts.csv')
    shared = old.merge(results, on='contrast_id', suffixes=('_old', '_new'), validate='one_to_one')
    assert len(shared) == 57
    for col in ['effect', 'standard_error', 'p', 'df', 'bootstrap_ci_low', 'bootstrap_ci_high']:
        np.testing.assert_allclose(shared[col+'_old'], shared[col+'_new'], atol=1e-12)
    out.mkdir()
    results.to_csv(out / 'all_scalar_contrasts.csv', index=False)
    results[results.family.eq('global_14')].to_csv(out / 'global_sari.csv', index=False)
    results[results.family.eq('local_78')].to_csv(out / 'local_sari.csv', index=False)
    (out / 'omnibus_sari.csv').write_bytes((PREVIOUS / 'results/omnibus_sari.csv').read_bytes())
    shared[['contrast_id', 'effect_new', 'q_bh_old', 'q_bh_new']].to_csv(out / 'shared_contrast_reconciliation.csv', index=False)
    np.save(out / 'bootstrap_contrasts.npy', draws)
    proof = dict(status='complete', model_configurations=162, response_instances=20142, source_clusters=335,
                 model_refitted=False, original_15_omnibus_tests_unchanged=True, global_contrasts=14, local_contrasts=78,
                 bootstrap_replicates=10000, bootstrap_seed=20261104, shared_contrasts_verified=57,
                 prior_outcomes_known=True, preregistered=False, new_inference_calls=0, new_metric_evaluations=0,
                 parent_completion_sha256=sha(PREVIOUS / 'results/complete.json'), code_plan_hashes=frozen['code_plan_hashes'],
                 output_hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in out.iterdir()})
    (out / 'complete.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(results[results.family.eq('global_14')][['contrast_id', 'effect', 'q_bh']].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.execute:
        execute()
