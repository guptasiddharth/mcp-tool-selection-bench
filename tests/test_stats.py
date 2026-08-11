from toolpick.stats import cluster_ci, paired_diff


def test_all_ones():
    est = cluster_ci([1.0] * 10, ["a"] * 5 + ["b"] * 5, seed=1)
    assert est.mean == 1.0
    assert est.lo == 1.0 and est.hi == 1.0
    assert est.clusters == 2


def test_all_zeros():
    est = cluster_ci([0.0] * 8, ["a", "b"] * 4, seed=1)
    assert est.mean == 0.0
    assert est.lo == 0.0 and est.hi == 0.0


def test_mixed_interval_bounds():
    vals = [1.0, 0.0] * 10
    est = cluster_ci(vals, (["a"] * 10 + ["b"] * 10), seed=2)
    assert 0.0 <= est.lo <= est.mean <= est.hi <= 1.0
    assert abs(est.mean - 0.5) < 1e-9


def test_paired_diff_detects_consistent_gap():
    a = {f"t{i}": 1.0 for i in range(20)}
    b = {f"t{i}": 0.0 for i in range(20)}
    clusters = {f"t{i}": ("a" if i < 10 else "b") for i in range(20)}
    pr = paired_diff(a, b, clusters, seed=3)
    assert pr.delta == 1.0
    assert pr.significant


def test_paired_diff_identical_is_not_significant():
    a = {f"t{i}": float(i % 2) for i in range(20)}
    b = dict(a)
    clusters = {f"t{i}": ("a" if i < 10 else "b") for i in range(20)}
    pr = paired_diff(a, b, clusters, seed=4)
    assert pr.delta == 0.0
    assert not pr.significant
