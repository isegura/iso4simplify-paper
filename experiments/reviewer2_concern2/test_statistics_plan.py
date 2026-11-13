"""Synthetic validation only. No research prediction files are opened."""
import unittest
import numpy as np
import pandas as pd
from prepare_statistics import configurations, build_contrasts, contrast
from statistics_core import fit_clustered, test_contrasts, adjust_by_family, cluster_bootstrap


class StatisticalPlanTests(unittest.TestCase):
    def test_balanced_margins_and_known_effect(self):
        cells = configurations()
        self.assertEqual(len(cells), 144)
        rows = build_contrasts(cells)
        self.assertEqual(len(rows), 43)
        means = cells.prompt.map({'minimal': 0, 'iso': 2, 'iso_examples': 3}).to_numpy(float)
        for condition in ['zero', 'one', 'few_random', 'few_metric']:
            weights = contrast(cells, {'condition': condition}, {'condition': 'zero'})
            self.assertAlmostEqual(float(weights @ means), 0.)
        iso = next(r for r in rows if r['contrast_id'] == 'iso_minus_baseline')
        self.assertAlmostEqual(float(iso['weights'] @ means), 2.)
        positive = iso['weights'][iso['weights'] > 0]
        by_condition = positive.groupby(cells.loc[positive.index, 'condition']).sum()
        np.testing.assert_allclose(by_condition.to_numpy(), [.25]*4)

    def test_ols_and_sandwich_against_expanded_rows(self):
        # Three documents; first has two rows (analogous to repeated PLABA IDs).
        values = [[1., 2., 3., 6.], [2., 5.], [4., 8.]]
        clusters, rows, outcomes = [], [], []
        for group, data in enumerate(values):
            for i, y in enumerate(data):
                clusters.append(group)
                rows.append(np.eye(2)[i % 2])
                outcomes.append(y)
        x, y, clusters = np.array(rows), np.array(outcomes), np.array(clusters)
        sums = np.zeros((3, 2)); counts = sums.copy()
        for i, group in enumerate(clusters):
            sums[group] += x[i]*y[i]
            counts[group] += x[i]
        beta, covariance = fit_clustered(sums, counts)
        expected = np.linalg.lstsq(x, y, rcond=None)[0]
        np.testing.assert_allclose(beta, expected)
        bread = np.linalg.inv(x.T @ x)
        residual = y-x@expected
        scores = np.array([x[clusters == g].T @ residual[clusters == g] for g in range(3)])
        expected_cov = 3/2 * (len(y)-1)/(len(y)-2) * bread @ (scores.T @ scores) @ bread
        np.testing.assert_allclose(covariance, expected_cov)
        result = test_contrasts(beta, covariance, [[-1, 1]], [2])
        self.assertGreater(result['effect'][0], 0)
        bootstrap, intervals = cluster_bootstrap(sums, counts, ['dataset']*3, [[-1, 1]], repetitions=200, seed=42)
        repeated, _ = cluster_bootstrap(sums, counts, ['dataset']*3, [[-1, 1]], repetitions=200, seed=42)
        np.testing.assert_array_equal(bootstrap, repeated)
        self.assertEqual(intervals.shape, (2, 1))

    def test_families_and_invalid_inputs(self):
        adjusted = adjust_by_family([.01, .04, .02], ['primary', 'primary', 'secondary'])
        np.testing.assert_allclose(adjusted, [.02, .04, .02])
        with self.assertRaises(ValueError):
            fit_clustered([[1., 0.], [2., 0.]], [[1, 0], [1, 0]])


if __name__ == '__main__':
    unittest.main()
