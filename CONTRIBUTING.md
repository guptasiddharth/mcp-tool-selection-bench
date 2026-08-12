# Contributing to ToolPick

Thanks for helping make agent tool selection measurable. The most useful
contributions are new domains and tasks with realistic distractors and policy
traps, since that is where real agents fail.

## Add a domain or tasks

1. Add or extend a server in `data/servers/<domain>.json`. Give it overlapping
   tools (a search vs a get, a read vs a metadata call) and at least one
   destructive tool, so selection is non-trivial.
2. Add tasks to `data/tasks/<domain>.jsonl`, one JSON object per line. Keep every
   task's `expected_tool` and every `forbidden_tool` inside that server. Cover
   the ambiguous cases: distractors, a policy trap (a tempting forbidden action),
   and a pressure scenario.
3. See `docs/METHODOLOGY.md` for the full task schema, including `expected_args`
   and `acceptable_tools`.

## Before you open a PR

Run the checks the way CI does:

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

The loader validates every task, so the suite tests fail if a tool name is wrong.

## Ground rules

- Keep tasks deterministic and gradeable with a golden answer. No task should
  need an LLM judge to score.
- Do not change the frozen numbers in `README.md` or `examples/results-sample.md`.
  Those record a specific run and stay reproducible.
- No em dashes in prose (house style).

By contributing you agree your work is released under the repository's MIT license.
