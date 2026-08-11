"""Turn one or more runs into a decision table an engineering lead can act on."""

from __future__ import annotations

from .stats import PairedResult, cluster_ci, paired_diff
from .types import RunResult

_METRICS = [
    ("correct", "Correct"),
    ("tool_selection", "Tool selection"),
    ("parameter_accuracy", "Parameter acc."),
    ("policy_adherence", "Policy adherence"),
]


def _values(run: RunResult, metric: str) -> tuple[list[float], list[str]]:
    vals, clus = [], []
    for r in run.results:
        vals.append(getattr(r.scores, metric))
        clus.append(r.domain)
    return vals, clus


def summarize(run: RunResult, *, seed: int = 0) -> dict:
    """Overall estimates (clustered by domain) plus a per-domain accuracy map."""
    out: dict = {"model": run.model, "n": len(run.results), "metrics": {}, "by_domain": {}}
    for key, _ in _METRICS:
        vals, clus = _values(run, key)
        est = cluster_ci(vals, clus, seed=seed)
        out["metrics"][key] = {"mean": est.mean, "lo": est.lo, "hi": est.hi}
    domains = sorted({r.domain for r in run.results})
    for d in domains:
        vals = [r.scores.correct for r in run.results if r.domain == d]
        out["by_domain"][d] = sum(vals) / len(vals) if vals else 0.0
    return out


def _fmt(m: dict) -> str:
    return f"{m['mean']:.2f} [{m['lo']:.2f}, {m['hi']:.2f}]"


def markdown(runs: list[RunResult], *, seed: int = 0) -> str:
    """A decision table across runs, with clustered CIs and a paired baseline diff."""
    if not runs:
        return "_No runs._\n"
    summaries = [summarize(r, seed=seed) for r in runs]

    lines: list[str] = []
    lines.append("# ToolPick results\n")
    lines.append(
        f"Suite `{runs[0].suite}` · {summaries[0]['n']} tasks · clustered by domain "
        f"(95% bootstrap CIs).\n"
    )

    # Decision table.
    header = "| Model | " + " | ".join(label for _, label in _METRICS) + " |"
    sep = "|" + "---|" * (len(_METRICS) + 1)
    lines.append(header)
    lines.append(sep)
    for run, s in zip(runs, summaries):
        cells = [_fmt(s["metrics"][key]) for key, _ in _METRICS]
        lines.append(f"| `{run.model}` | " + " | ".join(cells) + " |")
    lines.append("")

    # Per-domain correctness.
    domains = sorted({d for s in summaries for d in s["by_domain"]})
    lines.append("## Correct, by domain\n")
    lines.append("| Model | " + " | ".join(domains) + " |")
    lines.append("|" + "---|" * (len(domains) + 1))
    for run, s in zip(runs, summaries):
        cells = [f"{s['by_domain'].get(d, 0.0):.2f}" for d in domains]
        lines.append(f"| `{run.model}` | " + " | ".join(cells) + " |")
    lines.append("")

    # Paired comparison against the first run as baseline.
    if len(runs) > 1:
        base = runs[0]
        base_correct = {r.task_id: r.scores.correct for r in base.results}
        clusters = {r.task_id: r.domain for r in base.results}
        lines.append(f"## Paired vs baseline `{base.model}` (correct)\n")
        lines.append("| Model | Delta (paired, clustered CI) |")
        lines.append("|---|---|")
        for run in runs[1:]:
            other = {r.task_id: r.scores.correct for r in run.results}
            pr: PairedResult = paired_diff(other, base_correct, clusters, seed=seed)
            lines.append(f"| `{run.model}` | {pr} |")
        lines.append("")
        lines.append(
            "_A delta whose interval excludes zero is a real difference on this suite; "
            "one that crosses zero is noise, however large the point estimate looks._\n"
        )

    return "\n".join(lines)
