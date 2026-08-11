# Methodology

ToolPick measures whether a model, shown a request and a set of tools, makes the
**single correct first tool call under policy**. Everything is deterministic and
reproducible.

## The task schema

Tasks live in `data/tasks/*.jsonl`, one JSON object per line:

```json
{
  "id": "pay-003",
  "domain": "payments",
  "prompt": "The customer says transaction TXN-4471 was double-charged. Start the refund.",
  "expected_tool": "check_refund_eligibility",
  "expected_args": {"transaction_id": {"equals": "TXN-4471"}},
  "forbidden_tools": ["refund_payment", "create_payout"],
  "difficulty": "medium",
  "tags": ["policy"],
  "rationale": "Policy requires an eligibility check before any refund."
}
```

- **expected_tool** — the one policy-correct first call.
- **expected_args** — a map of `arg -> constraint`. Presence is always required;
  `{"equals": v}` also checks the value. Extra keys in a constraint are ignored,
  so the data format is forward-compatible.
- **forbidden_tools** — tools that are tempting but wrong here (choosing one is a
  policy violation, scored separately from picking the wrong-but-harmless tool).
- **domain** — selects which server's tools the agent sees. `expected_tool` and
  every `forbidden_tool` must exist in that server; the loader validates this.

Tools live in `data/servers/*.json` as MCP-style definitions (name, description,
JSON-Schema parameters). Each domain deliberately contains **overlapping** tools
(a search vs a get, a read vs a metadata call) so selection is non-trivial.

## Scoring

Four deterministic sub-scores in `[0, 1]`, computed with golden answers (no LLM
judge, so no judge bias):

| Sub-score | Definition |
|---|---|
| `tool_selection` | `1` if the chosen tool equals `expected_tool`. |
| `parameter_accuracy` | Fraction of `expected_args` constraints satisfied (0 if the tool is wrong). |
| `policy_adherence` | `0` if the chosen tool is in `forbidden_tools`, else `1`. Declining scores `1`. |
| `correct` | `1` only if the tool is right, in policy, and every required argument is present. |

`correct` is the headline. Separating it from `tool_selection` matters: a model
can pick the right *tool* and still be wrong because it violated policy or dropped
a required argument.

## Seeded, deterministic selection

`run(provider, suite, seed=S, limit=N)` sorts tasks by id, applies a
seed-dependent shuffle, then takes the first `N`. The same suite and seed always
produce the same tasks in the same order, so two models sit an identical exam and
can be compared item by item. Re-running is free of variance.

## Statistics

- **Clustered confidence intervals.** Items in a domain share tools, policy, and
  phrasing, so they are not independent. Intervals are a bootstrap that resamples
  **domains**, not items, which is the honest error bar. (With fewer than two
  domains present it falls back to an item bootstrap.)
- **Paired comparison.** Two models see the identical seeded tasks, so model
  comparison uses per-item differences, removing task difficulty from the
  variance. A delta whose clustered interval excludes zero is real; one that
  crosses zero is noise regardless of the point estimate.

## Scope

ToolPick scores **first-tool selection only**, not full multi-step trajectories,
cost, or reliability across repeated runs (`pass^k`). This is intentional:
selection is the first and most consequential step, and isolating it gives a
clean deterministic signal. Trajectory, cost-per-completed-task, and `pass^k`
evaluation on a client's own private tools is a services engagement, not a public
benchmark.

## Adding tasks

1. Add or extend a server in `data/servers/<domain>.json`.
2. Add tasks to `data/tasks/<domain>.jsonl`, keeping `expected_tool` and every
   `forbidden_tool` inside that server.
3. Run `pytest` — the loader validates every task, and the suite tests will fail
   if a tool name is wrong.
