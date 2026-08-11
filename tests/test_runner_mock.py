from pathlib import Path

from toolpick import get_provider, load_suite, run, summarize

DATA = Path(__file__).resolve().parents[1] / "data"


def test_suite_loads_and_validates():
    suite = load_suite(DATA)
    assert set(suite.domains) == {"payments", "support", "files"}
    assert len(suite.tasks) >= 30


def _without_latency(results):
    out = []
    for x in results:
        d = x.to_dict()
        d.pop("latency_ms", None)  # wall-clock, not part of the deterministic result
        out.append(d)
    return out


def test_mock_run_is_deterministic():
    suite = load_suite(DATA)
    r1 = run(get_provider("mock", seed=0), suite, seed=0)
    r2 = run(get_provider("mock", seed=0), suite, seed=0)
    assert _without_latency(r1.results) == _without_latency(r2.results)


def test_scores_in_range_and_summary_shape():
    suite = load_suite(DATA)
    result = run(get_provider("mock", seed=0), suite, seed=0)
    assert len(result.results) == len(suite.tasks)
    for r in result.results:
        for v in (r.scores.tool_selection, r.scores.parameter_accuracy, r.scores.policy_adherence, r.scores.correct):
            assert 0.0 <= v <= 1.0
    s = summarize(result)
    assert set(s["by_domain"]) == {"payments", "support", "files"}
    assert 0.0 <= s["metrics"]["correct"]["mean"] <= 1.0


def test_limit_and_seed_select_subset():
    suite = load_suite(DATA)
    result = run(get_provider("mock", seed=0), suite, seed=0, limit=5)
    assert len(result.results) == 5
