"""Confidence intervals and paired comparison, with clustering.

Tasks in this benchmark are not independent: items in the same domain share tools,
policies, and phrasing, so treating them as independent understates the error and
manufactures false precision. Every interval here is a *cluster* bootstrap, where
the resampling unit is the domain, not the item.

Model comparison uses paired per-item differences (both models see the identical
seeded task), which removes task difficulty from the variance and is far more
powerful than comparing two independent averages.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Estimate:
    mean: float
    lo: float
    hi: float
    n: int
    clusters: int

    def __str__(self) -> str:
        return f"{self.mean:.3f} [{self.lo:.3f}, {self.hi:.3f}]"


def _grouped(values: list[float], clusters: list[str]) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = {}
    for v, c in zip(values, clusters):
        groups.setdefault(c, []).append(v)
    return groups


def cluster_ci(
    values: list[float],
    clusters: list[str],
    *,
    alpha: float = 0.05,
    iterations: int = 5000,
    seed: int = 0,
) -> Estimate:
    """Point estimate and (1-alpha) percentile CI via a clustered bootstrap."""
    if not values:
        return Estimate(0.0, 0.0, 0.0, 0, 0)
    groups = _grouped(values, clusters)
    keys = list(groups)
    mean = sum(values) / len(values)
    if len(keys) < 2:
        # Not enough clusters to bootstrap between; fall back to item bootstrap.
        return _item_ci(values, alpha=alpha, iterations=iterations, seed=seed, clusters=len(keys))

    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(iterations):
        pool: list[float] = []
        for _ in range(len(keys)):
            pool.extend(groups[keys[rng.randrange(len(keys))]])
        means.append(sum(pool) / len(pool))
    means.sort()
    lo = means[int((alpha / 2) * iterations)]
    hi = means[min(int((1 - alpha / 2) * iterations), iterations - 1)]
    return Estimate(mean, lo, hi, len(values), len(keys))


def _item_ci(values, *, alpha, iterations, seed, clusters) -> Estimate:
    rng = random.Random(seed)
    n = len(values)
    mean = sum(values) / n
    means = []
    for _ in range(iterations):
        pool = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(pool) / n)
    means.sort()
    lo = means[int((alpha / 2) * iterations)]
    hi = means[min(int((1 - alpha / 2) * iterations), iterations - 1)]
    return Estimate(mean, lo, hi, n, clusters)


@dataclass(frozen=True)
class PairedResult:
    delta: float          # mean(a) - mean(b) over shared items
    lo: float
    hi: float
    significant: bool     # does the CI exclude zero?
    n: int

    def __str__(self) -> str:
        star = " (significant)" if self.significant else " (not significant)"
        return f"delta {self.delta:+.3f} [{self.lo:+.3f}, {self.hi:+.3f}]{star}"


def paired_diff(
    a: dict[str, float],
    b: dict[str, float],
    clusters: dict[str, str],
    *,
    alpha: float = 0.05,
    iterations: int = 5000,
    seed: int = 0,
) -> PairedResult:
    """Clustered bootstrap of the per-item difference a - b over shared task ids."""
    shared = [k for k in a if k in b]
    if not shared:
        return PairedResult(0.0, 0.0, 0.0, False, 0)
    diffs = {k: a[k] - b[k] for k in shared}
    values = [diffs[k] for k in shared]
    clabels = [clusters.get(k, k) for k in shared]
    est = cluster_ci(values, clabels, alpha=alpha, iterations=iterations, seed=seed)
    significant = est.lo > 0 or est.hi < 0
    return PairedResult(est.mean, est.lo, est.hi, significant, len(shared))
