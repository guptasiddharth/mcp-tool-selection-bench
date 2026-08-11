"""Run a provider over a suite, deterministically.

Selection is seeded: the same suite and seed always pick the same tasks in the
same order, so any two runs (two models, or one model twice) are comparable item
by item. Each attempt is scored immediately, but only the raw choice and scores are
kept, so a decision rule can change later without re-running anything.

Runs may execute concurrently (I/O-bound API calls). Concurrency never affects the
scored result or its order; results are always assembled in the seeded task order,
so a run stays reproducible regardless of how many workers execute it.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import scoring
from .providers import DEFAULT_SYSTEM
from .providers.base import Provider
from .suites.loader import Suite
from .types import RunResult, Task, TaskResult


def _run_one(provider: Provider, suite: Suite, task: Task, cross_domain: bool, system: str) -> TaskResult:
    tools = suite.tools_for(task, cross_domain=cross_domain)
    t0 = time.perf_counter()
    error = None
    call = None
    try:
        call = provider.select_tool(system, task.prompt, tools)
    except Exception as e:  # noqa: BLE001 - record, never crash the run
        error = f"{type(e).__name__}: {e}"
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return TaskResult(
        task_id=task.id,
        domain=task.domain,
        difficulty=task.difficulty,
        tags=task.tags,
        call=call,
        scores=scoring.score(task, call),
        latency_ms=latency_ms,
        error=error,
    )


def run(
    provider: Provider,
    suite: Suite,
    *,
    seed: int = 0,
    limit: int | None = None,
    cross_domain: bool = False,
    concurrency: int = 1,
    system: str = DEFAULT_SYSTEM,
) -> RunResult:
    tasks = sorted(suite.tasks, key=lambda t: t.id)
    order = list(range(len(tasks)))
    random.Random(seed).shuffle(order)  # fixed, seed-dependent order
    if limit is not None:
        order = order[:limit]
    selected = [tasks[i] for i in order]

    if concurrency <= 1:
        results = [_run_one(provider, suite, t, cross_domain, system) for t in selected]
    else:
        # Execute concurrently but keep results in the seeded order (by index).
        results_by_index: dict[int, TaskResult] = {}
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(_run_one, provider, suite, t, cross_domain, system): i
                for i, t in enumerate(selected)
            }
            for fut, idx in futures.items():
                results_by_index[idx] = fut.result()
        results = [results_by_index[i] for i in range(len(selected))]

    return RunResult(
        provider=provider.name,
        model=provider.model,
        seed=seed,
        suite=suite.name,
        created_at=datetime.now(timezone.utc).isoformat(),
        results=tuple(results),
        meta={"cross_domain": cross_domain, "n_tasks": len(results), "concurrency": concurrency},
    )
