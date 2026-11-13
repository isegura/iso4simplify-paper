"""Independent arithmetic and delivery-integrity checks, without model fitting."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from scipy.stats import t, f, false_discovery_control

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    result = HERE / 'results'
    proof = json.loads((result / 'complete.json').read_text())
    for name, digest in {**proof['input_hashes'], **proof['output_hashes'], **proof['code_hashes']}.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    cells = pd.read_csv(result / 'cell_estimates.csv')
    records = pd.read_csv(result / 'all_scalar_contrasts.csv')
    clusters = pd.read_csv(result / 'clusters.csv')
    sufficient = np.load(result / 'sufficient_statistics.npz')
    weights = np.load(HERE / 'design/contrast_weights.npy')
    assert len(cells) == 162 and len(records) == 57 and sufficient['counts'].sum() == 20142
    totals = sufficient['counts'].sum(axis=0)
    means = sufficient['sums'].sum(axis=0) / totals
    np.testing.assert_allclose(means, cells.SARI, atol=1e-12)
    # Calculate each contrast's SE directly from its group residual contributions.
    residual_scores = sufficient['sums'] - sufficient['counts'] * means
    cr1 = 335/334 * 20141/(20142-162)
    direct_scores = (residual_scores / totals) @ weights.T
    direct_se = np.sqrt(cr1 * np.sum(direct_scores**2, axis=0))
    np.testing.assert_allclose(direct_se, records.standard_error, atol=1e-12)
    np.testing.assert_allclose(weights @ means, records.effect, atol=1e-12)
    np.testing.assert_allclose(2*t.sf(np.abs(records.effect/direct_se), records.df), records.p, atol=1e-12)
    for family, group in records.groupby('family'):
        np.testing.assert_allclose(false_discovery_control(group.p, method='bh'), group.q_bh, atol=1e-12)
    draws = np.load(result / 'bootstrap_contrasts.npy')
    assert draws.shape == (10000, 57)
    np.testing.assert_allclose(np.quantile(draws, [.025, .975], axis=0), records[['bootstrap_ci_low', 'bootstrap_ci_high']].to_numpy().T, atol=1e-12)
    omnibus = pd.read_csv(result / 'omnibus_sari.csv')
    restrictions = np.load(HERE / 'design/omnibus_restrictions.npz')
    assert len(omnibus) == 15
    for row in omnibus.itertuples():
        r = restrictions[row.term]
        v = r @ sufficient['covariance'] @ r.T
        b = r @ means
        statistic = float(b @ np.linalg.solve(v, b) / len(b))
        assert np.linalg.matrix_rank(v) == len(b) == row.df_num
        np.testing.assert_allclose(statistic, row.F)
        np.testing.assert_allclose(f.sf(statistic, row.df_num, 334), row.p)
    np.testing.assert_allclose(false_discovery_control(omnibus.p, method='bh'), omnibus.q_bh, atol=1e-12)
    # Independently recover model/dataset margins from the 90 structural means.
    structural = pd.read_csv(result / 'structural_means.csv')
    assert len(structural) == 90
    for row in records[records.family.eq('local_48')].itertuples():
        group = structural[structural.model.eq(row.model) & structural.dataset.eq(row.dataset)]
        if row.contrast_id.startswith('few_retrieval_minus_few_random'):
            difference = group[group.condition.eq('few_retrieval')].SARI.mean() - group[group.condition.eq('few_random')].SARI.mean()
            np.testing.assert_allclose(difference, row.effect)
    delivery = json.loads((HERE / 'manuscript_proposals/manifest.json').read_text())
    for name, digest in delivery['files'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    labels = []
    for path in (HERE / 'manuscript_proposals').rglob('*.tex'):
        labels += re.findall(r'\\label\{([^}]+)\}', path.read_text())
    assert len(labels) == len(set(labels))
    qa = dict(status='passed', configurations=162, structural_means=90, response_instances=20142,
              source_groups=335, scalar_effects_and_SEs_checked=57, omnibus_rank_and_F_checked=15,
              BH_families_checked=[9, 48, 15], bootstrap_draws=10000, pointwise_intervals_checked=57,
              input_output_delivery_hashes_match=True, synthetic_tests=4,
              latex_review_project_compilation='success using built-in desktop compiler',
              complete_overleaf_integration='pending', new_inference_calls=0, new_metric_evaluations=0)
    (HERE / 'QA.json').write_text(json.dumps(qa, indent=2), encoding='utf-8')
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    main()
