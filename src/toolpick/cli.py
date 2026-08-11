"""ToolPick command line: run a model, report results, inspect the suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, report
from .providers import get_provider
from .runner import run as run_suite
from .suites.loader import load_suite
from .types import RunResult, Scores, TaskResult, ToolCall


def _cmd_list(args: argparse.Namespace) -> int:
    suite = load_suite(args.data)
    print(f"Suite: {suite.name}")
    print(f"Domains: {', '.join(suite.domains)}")
    for name, server in suite.servers.items():
        print(f"  server {name}: {len(server.tools)} tools")
    print(f"Tasks: {len(suite.tasks)}")
    by_diff: dict[str, int] = {}
    for t in suite.tasks:
        by_diff[t.difficulty] = by_diff.get(t.difficulty, 0) + 1
    print("  by difficulty: " + ", ".join(f"{k}={v}" for k, v in sorted(by_diff.items())))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    suite = load_suite(args.data)
    provider = get_provider(args.provider, model=args.model, seed=args.seed)
    result = run_suite(
        provider, suite, seed=args.seed, limit=args.limit,
        cross_domain=args.cross_domain, concurrency=args.concurrency,
    )
    out = args.out or f"results/{provider.name}-{provider.model.replace('/', '_')}-seed{args.seed}.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result.to_dict(), indent=2))

    s = report.summarize(result, seed=args.seed)
    m = s["metrics"]["correct"]
    print(f"Ran {provider.model} on {s['n']} tasks.")
    print(f"  correct:          {m['mean']:.3f} [{m['lo']:.3f}, {m['hi']:.3f}]")
    print(f"  tool selection:   {s['metrics']['tool_selection']['mean']:.3f}")
    print(f"  policy adherence: {s['metrics']['policy_adherence']['mean']:.3f}")
    print(f"  -> {out}")
    return 0


def _load_run(path: str) -> RunResult:
    d = json.loads(Path(path).read_text())
    results = tuple(
        TaskResult(
            task_id=r["task_id"],
            domain=r["domain"],
            difficulty=r.get("difficulty", "medium"),
            tags=tuple(r.get("tags", [])),
            call=None if r["call"] is None else ToolCall(r["call"]["tool"], r["call"]["arguments"]),
            scores=Scores(**r["scores"]),
            latency_ms=r.get("latency_ms", 0.0),
            error=r.get("error"),
        )
        for r in d["results"]
    )
    return RunResult(
        provider=d["provider"], model=d["model"], seed=d["seed"], suite=d["suite"],
        created_at=d["created_at"], results=results, meta=d.get("meta", {}),
    )


def _cmd_report(args: argparse.Namespace) -> int:
    runs = [_load_run(p) for p in args.runs]
    md = report.markdown(runs, seed=args.seed)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md)
        print(f"Wrote {args.out}")
    else:
        print(md)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="toolpick", description=__doc__)
    p.add_argument("--version", action="version", version=f"toolpick {__version__}")
    p.add_argument("--data", type=Path, default=None, help="Path to the data/ directory.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="Show the suite: domains, tools, task counts.")
    pl.set_defaults(func=_cmd_list)

    pr = sub.add_parser("run", help="Run a provider over the suite.")
    pr.add_argument("--provider", default="mock", help="mock (default) or litellm.")
    pr.add_argument("--model", default=None, help="Model id for the litellm provider.")
    pr.add_argument("--seed", type=int, default=0)
    pr.add_argument("--limit", type=int, default=None, help="Run only N seeded tasks.")
    pr.add_argument("--cross-domain", action="store_true", help="Expose all servers' tools.")
    pr.add_argument("--concurrency", type=int, default=1, help="Parallel workers for API calls.")
    pr.add_argument("--out", default=None, help="Output JSON path.")
    pr.set_defaults(func=_cmd_run)

    prep = sub.add_parser("report", help="Build a markdown decision table from run JSON.")
    prep.add_argument("runs", nargs="+", help="One or more run JSON files.")
    prep.add_argument("--seed", type=int, default=0, help="Bootstrap seed.")
    prep.add_argument("--out", default=None, help="Output markdown path (else stdout).")
    prep.set_defaults(func=_cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
