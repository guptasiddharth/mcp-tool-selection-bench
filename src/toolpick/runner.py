"""Run a provider over a suite, deterministically.

Selection is seeded: the same suite and seed always pick the same tasks in the
same order, so any two runs (two models, or one model twice) are comparable item
by item. Each attempt is scored immediately, but only the raw choice and scores are
kept, so a decision rule can change later without re-running anything.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone

from . import scoring
from .providers import DEFAULT_SYSTEM
from .providers.base import Provider
from .suites.loader import Suite
from .types import RunResult, TaskResult


def run(
    provider: Provider,
    suite: Suite,
    *,
    seed: int = 0,
    limit: int | None = None,
    cross_domain: bool = False,
    system: str = DEFAULT_SYSTEM,
) -> RunResult:
    tasks = sorted(suite.tasks, key=lambda t: t.id)
    order = list(range(len(tasks)))
    random.Random(seed).shuffle(order)  # fixed, seed-dependent order
    if limit is not None:
        order = order[:limit]
    selected = [tasks[i] for i in order]

    results: list[TaskResult] = []
    for task in selected:
        tools = suite.tools_for(task, cross_domain=cross_domain)
        t0 = time.perf_counter()
        error = None
        call = None
        try:
            call = provider.select_tool(system, task.prompt, tools)
        except Exception as e:  # noqa: BLE001 - record, never crash the run
            error = f"{type(e).__name__}: {e}"
        latency_ms = (time.perf_counter() - t0) * 1000.0
        scores = scoring.score(task, call)
        results.append(
            TaskResult(
                task_id=task.id,
                domain=task.domain,
                difficulty=task.difficulty,
                tags=task.tags,
                call=call,
                scores=scores,
                latency_ms=latency_ms,
                error=error,
            )
        )

    return RunResult(
        provider=provider.name,
        model=provider.model,
        seed=seed,
        suite=suite.name,
        created_at=datetime.now(timezone.utc).isoformat(),
        results=tuple(results),
        meta={"cross_domain": cross_domain, "n_tasks": len(results)},
    )
