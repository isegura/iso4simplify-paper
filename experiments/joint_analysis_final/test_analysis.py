"""Synthetic validation of the unified design and clustered inference."""
import itertools
import unittest
import numpy as np
from scipy.stats import t, f

import run_analysis as r


class JointTests(unittest.TestCase):
    def test_structure_balanced_margins_and_known_effects(self):
        cells = r.configurations()
        self.assertEqual(len(cells), 162)
        self.assertEqual(len(cells.groupby(list(r.LEVELS))), 90)
        records, w = r.scalar_contrasts(cells)
        self.assertEqual(records.groupby('family').size().to_dict(), {'global_9': 9, 'local_48': 48})
        truth = cells.prompt.map({'minimal': 0., 'iso': 2., 'iso_examples': 3.}).to_numpy()
        np.testing.assert_allclose((w @ truth)[:3], [2, 3, 1])
        np.testing.assert_allclose(w.sum(axis=1), 0, atol=1e-15)
        np.testing.assert_allclose(np.where(w > 0, w, 0).sum(axis=1), 1)
        positive = w[0].copy()
        positive[positive < 0] = 0
        totals = {c: positive[cells.condition.eq(c)].sum() for c in r.LEVELS['condition']}
        np.testing.assert_allclose(list(totals.values()), [.2] * 5)
        for _, group in cells.groupby(list(r.LEVELS)):
            if len(group) == 3:
                np.testing.assert_allclose(positive[group.index], [positive[group.index].sum() / 3] * 3)

    def test_full_factorial_hypotheses_and_interaction(self):
        cells = r.configurations()
        hypotheses = r.omnibus_restrictions(cells)
        self.assertEqual(len(hypotheses), 15)
        self.assertEqual(sum(np.linalg.matrix_rank(a) for _, a in hypotheses), 89)
        truth = (2 * cells.prompt.eq('iso').astype(float) +
                 3 * (cells.prompt.eq('iso') & cells.model.eq('mixtral')).astype(float)).to_numpy()
        restrictions = dict(hypotheses)
        expected = restrictions['model*prompt'] @ truth
        np.testing.assert_allclose(expected, [3, 0], atol=1e-14)
        np.testing.assert_allclose(restrictions['dataset*prompt'] @ truth, 0, atol=1e-14)
        np.testing.assert_allclose(restrictions['model*prompt*condition'] @ truth, 0, atol=1e-14)
        # Same null with another nonsingular row basis produces the same F/p.
        v = np.eye(162)
        a = restrictions['model*prompt']
        b = np.array([[2., 1.], [-1., 1.]]) @ a
        original = r.omnibus_test(truth, v, a, 40)
        transformed = r.omnibus_test(truth, v, b, 40)
        self.assertAlmostEqual(original['F'], transformed['F'])
        self.assertAlmostEqual(original['p'], transformed['p'])

    def test_expanded_ols_cluster_covariance_and_wald(self):
        rng = np.random.default_rng(712)
        groups, p = 45, 18
        counts = np.ones((groups, p))
        counts[0] = 2  # duplicate source rows stay in the same cluster
        values = rng.normal(size=(groups, p))
        sums = values * counts
        means, covariance = r.fit_clustered(sums, counts)
        xs, ys, gs = [], [], []
        for g in range(groups):
            for c in range(p):
                for _ in range(int(counts[g, c])):
                    xs.append(np.eye(p)[c]); ys.append(values[g, c]); gs.append(g)
        x, y, group = np.array(xs), np.array(ys), np.array(gs)
        beta = np.linalg.lstsq(x, y, rcond=None)[0]
        scores = np.array([x[group == g].T @ (y[group == g] - x[group == g] @ beta) for g in range(groups)])
        bread = np.linalg.inv(x.T @ x)
        cov = groups / (groups-1) * (len(y)-1)/(len(y)-p) * bread @ scores.T @ scores @ bread
        np.testing.assert_allclose(means, beta, atol=1e-14)
        np.testing.assert_allclose(covariance, cov, atol=1e-14)
        a = np.zeros((2, p)); a[0, [0, 1]] = [-1, 1]; a[1, [0, 2]] = [-1, 1]
        expected = float((a @ beta) @ np.linalg.inv(a @ cov @ a.T) @ (a @ beta) / 2)
        actual = r.omnibus_test(means, covariance, a, groups-1)
        self.assertAlmostEqual(expected, actual['F'])
        self.assertAlmostEqual(f.sf(expected, 2, groups-1), actual['p'])
        one = r.omnibus_test(means, covariance, a[:1], groups-1)
        effect = float(a[0] @ beta)
        se = float(np.sqrt(a[0] @ cov @ a[0]))
        self.assertAlmostEqual(one['p'], 2*t.sf(abs(effect/se), groups-1))

    def test_bootstrap_pairing_and_reproducibility(self):
        sums = np.array([[1, 3], [4, 8], [3, 5], [4, 6]], float)
        counts = np.array([[1, 1], [2, 2], [1, 1], [1, 1]], float)
        w = np.array([[-1., 1.]])
        first, ci = r.cluster_bootstrap(sums, counts, ['a']*4, w, repetitions=100, seed=20261104)
        second, _ = r.cluster_bootstrap(sums, counts, ['a']*4, w, repetitions=100, seed=20261104)
        # A difference of exactly two per source row remains exactly two in every group resample.
        np.testing.assert_allclose(first, 2)
        np.testing.assert_array_equal(first, second)


if __name__ == '__main__':
    unittest.main()
