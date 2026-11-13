"""Conditional joint cell-means regression; no file reads or model generation.

Inputs: sums and counts for every document cluster x observed configuration.
Keeping all configurations of each cluster together preserves pairing.
"""
import numpy as np
from scipy.stats import t, false_discovery_control


def fit_clustered(sums, counts):
    sums = np.asarray(sums, dtype=float)
    counts = np.asarray(counts, dtype=float)
    if sums.ndim != 2 or sums.shape != counts.shape or not np.isfinite(sums).all() or not np.isfinite(counts).all():
        raise ValueError('Invalid cluster/cell sufficient statistics')
    if (counts < 0).any() or not np.equal(counts, np.floor(counts)).all() or (sums[counts == 0] != 0).any():
        raise ValueError('Counts must be nonnegative integers; empty cells have zero sum')
    n_cell = counts.sum(axis=0)
    n, p = int(n_cell.sum()), sums.shape[1]
    groups = int(np.count_nonzero(counts.sum(axis=1)))
    if groups <= 1 or n <= p or (n_cell <= 0).any():
        raise ValueError('Insufficient clusters or absent configurations')
    means = sums.sum(axis=0) / n_cell
    cluster_scores = sums - counts * means
    scaled = cluster_scores / n_cell
    correction = groups / (groups - 1) * (n - 1) / (n - p)
    covariance = correction * scaled.T @ scaled
    return means, covariance


def test_contrasts(means, covariance, weights, degrees_of_freedom):
    weights = np.asarray(weights, dtype=float)
    effects = weights @ means
    variances = np.einsum('ij,jk,ik->i', weights, covariance, weights)
    if not np.isfinite(variances).all() or (variances <= 0).any():
        raise ValueError('Nonpositive/nonfinite contrast variance: inspect, do not replace test')
    standard_errors = np.sqrt(variances)
    degrees = np.broadcast_to(np.asarray(degrees_of_freedom, dtype=float), effects.shape)
    if (degrees < 1).any():
        raise ValueError('Invalid degrees of freedom')
    p_values = 2 * t.sf(np.abs(effects / standard_errors), degrees)
    radius = t.ppf(.975, degrees) * standard_errors
    return dict(effect=effects, standard_error=standard_errors, p=p_values,
                t_ci_low=effects-radius, t_ci_high=effects+radius)


def adjust_by_family(p_values, families):
    p_values = np.asarray(p_values, dtype=float)
    families = np.asarray(families)
    if len(p_values) != len(families):
        raise ValueError('Family labels mismatch')
    result = np.empty_like(p_values)
    for family in np.unique(families):
        mask = families == family
        result[mask] = false_discovery_control(p_values[mask], method='bh')
    return result


def cluster_bootstrap(sums, counts, datasets, weights, repetitions=10000, seed=20261023):
    sums, counts = np.asarray(sums, float), np.asarray(counts, float)
    fit_clustered(sums, counts)
    datasets = np.asarray(datasets)
    weights = np.asarray(weights, float)
    if len(datasets) != sums.shape[0] or repetitions < 2:
        raise ValueError('Invalid bootstrap groups/repetitions')
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(datasets == name) for name in sorted(set(datasets))]
    if any(len(group) < 2 for group in groups):
        raise ValueError('At least two document clusters per dataset are required')
    effects = np.empty((repetitions, weights.shape[0]))
    # Each draw samples whole document clusters within dataset. Multinomial
    # multiplicities are exactly the counts from sampling G indices with replacement.
    for start in range(0, repetitions, 128):
        batch = min(128, repetitions-start)
        multiplicities = np.zeros((batch, len(datasets)))
        for group in groups:
            multiplicities[:, group] = rng.multinomial(len(group), np.full(len(group), 1/len(group)), size=batch)
        denominator = multiplicities @ counts
        if (denominator <= 0).any():
            raise ValueError('Absent bootstrap cell: inspect design instead of discarding replicate')
        means = (multiplicities @ sums) / denominator
        effects[start:start+batch] = means @ weights.T
    return effects, np.quantile(effects, [.025, .975], axis=0)
