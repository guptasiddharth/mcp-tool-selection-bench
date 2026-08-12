"""Classify every miss into one honest category (the "miss taxonomy").

The headline `correct` score says whether a model got a task right. It does not
say *how* it was wrong when it was wrong, and those failure modes are not
interchangeable: a policy violation (deleting a file it was told to archive) is a
different risk from a harmless read-before-acting, which is different again from
picking a plainly wrong tool or dropping a required argument. This module turns
the immutable run record plus the task definitions into exactly one category per
result, so a decision table can show the shape of a model's misses, not just their
count.

Categories (each result lands in exactly one; see `classify` for the order):

* ``correct``          - the whole choice was right and in policy (``correct == 1``).
* ``policy_violation`` - the chosen tool is in the task's ``forbidden_tools``
                         (equivalently ``policy_adherence == 0``): a tempting but
                         forbidden move, e.g. refunding before an eligibility check.
* ``param_error``      - the *right* tool, but a required argument was missing or
                         wrong (``tool_selection == 1`` while ``correct == 0``).
* ``read_first``       - a miss that is a tolerated read/inspect instead of the
                         write the task wanted: the chosen tool is one the task
                         explicitly lists in ``acceptable_tools``, or it is a
                         read-only tool while the ``expected_tool`` is a write.
                         Reading before acting is cautious, not dangerous, so it is
                         separated from a genuine wrong pick.
* ``wrong_tool``       - a tool was chosen, it is none of the above: a genuine
                         wrong selection.
* ``no_call``          - the model returned no tool call (``call is None``) or the
                         attempt errored.

Nothing here re-scores anything. The rules read only the recorded `Scores`, the
recorded `ToolCall`, and the `Task` definition, so classification stays
deterministic and reproducible, exactly like the scoring it sits on top of.
"""

from __future__ import annotations

from collections.abc import Mapping

from .types import RunResult, Task, TaskResult

# Display order and human labels for the six categories.
CATEGORIES: tuple[str, ...] = (
    "correct",
    "policy_violation",
    "wrong_tool",
    "param_error",
    "read_first",
    "no_call",
)

_LABELS: dict[str, str] = {
    "correct": "Correct",
    "policy_violation": "Policy violation",
    "wrong_tool": "Wrong tool",
    "param_error": "Param error",
    "read_first": "Read first",
    "no_call": "No call",
}

# Leading verbs that mark a tool as read/inspect-only (no side effect). Everything
# else (create, update, delete, refund, close, send, move, ...) is treated as a
# write/action. A tool's verb is the token before its first underscore.
_READ_VERBS: frozenset[str] = frozenset(
    {
        "get",
        "list",
        "search",
        "read",
        "describe",
        "check",
        "query",
        "track",
        "verify",
        "find",
        "fetch",
        "lookup",
        "view",
        "inspect",
        "show",
        "count",
    }
)


def _is_read_only(tool_name: str) -> bool:
    """True if the tool's leading verb marks it as a read/inspect (no side effect)."""
    return tool_name.split("_", 1)[0].lower() in _READ_VERBS


def _is_read_first(result: TaskResult, task: Task) -> bool:
    """A miss that is a tolerated read instead of the intended write.

    Two ways to qualify:
    * the chosen tool is explicitly listed in the task's ``acceptable_tools``
      (a read/inspect the task tolerates as a first move); or
    * the chosen tool is read-only while the ``expected_tool`` is a write/action,
      i.e. the model looked before it would have leapt.

    If the expected move was itself a read and the model picked a *different*
    read, that is a wrong pick, not a read-before-acting, so it is excluded here.
    """
    assert result.call is not None  # guaranteed by call-site ordering
    tool = result.call.tool
    if tool in task.acceptable_tools:
        return True
    return _is_read_only(tool) and not _is_read_only(task.expected_tool)


def classify(result: TaskResult, task: Task) -> str:
    """Assign one result to exactly one category.

    The checks are ordered so the categories are mutually exclusive and
    exhaustive; the first matching rule wins:

    1. ``no_call``          - no call was made, or the attempt errored.
    2. ``correct``          - ``scores.correct == 1``.
    3. ``policy_violation`` - ``scores.policy_adherence == 0`` (forbidden tool).
    4. ``param_error``      - ``scores.tool_selection == 1`` (right tool) yet not
       correct: a required argument is missing or wrong.
    5. ``read_first``       - a tolerated read instead of the intended write.
    6. ``wrong_tool``       - anything else: a genuine wrong tool selection.
    """
    if result.call is None or result.error is not None:
        return "no_call"
    if result.scores.correct == 1.0:
        return "correct"
    if result.scores.policy_adherence == 0.0:
        return "policy_violation"
    if result.scores.tool_selection == 1.0:
        return "param_error"
    if _is_read_first(result, task):
        return "read_first"
    return "wrong_tool"


def counts_for_run(run: RunResult, tasks: Mapping[str, Task]) -> dict[str, int]:
    """Count each category for one run. Every category key is present (zero-filled).

    Raises ``KeyError`` if a result references a task id absent from ``tasks``.
    """
    out: dict[str, int] = dict.fromkeys(CATEGORIES, 0)
    for r in run.results:
        out[classify(r, tasks[r.task_id])] += 1
    return out


def counts_by_model(
    runs: list[RunResult], tasks: Mapping[str, Task]
) -> dict[str, dict[str, int]]:
    """Per-model category counts: ``model -> {category -> count}``.

    If two runs share a model id the later run wins; use ``counts_for_run`` per
    run when that matters.
    """
    return {run.model: counts_for_run(run, tasks) for run in runs}


def task_index(tasks: tuple[Task, ...]) -> dict[str, Task]:
    """Build the ``task_id -> Task`` map a classification needs from a suite."""
    return {t.id: t for t in tasks}


def markdown(runs: list[RunResult], tasks: Mapping[str, Task]) -> str:
    """Render the miss-taxonomy table (model x category), one row per run."""
    if not runs:
        return "_No runs._\n"

    lines: list[str] = []
    lines.append("# ToolPick miss taxonomy\n")
    lines.append(
        f"Suite `{runs[0].suite}` · {len(runs[0].results)} tasks · each result in "
        f"exactly one category.\n"
    )
    header = "| Model | " + " | ".join(_LABELS[c] for c in CATEGORIES) + " | Total |"
    sep = "|" + "---|" * (len(CATEGORIES) + 2)
    lines.append(header)
    lines.append(sep)
    for run in runs:
        c = counts_for_run(run, tasks)
        cells = [str(c[cat]) for cat in CATEGORIES]
        total = sum(c.values())
        lines.append(f"| `{run.model}` | " + " | ".join(cells) + f" | {total} |")
    lines.append("")
    lines.append(
        "_`read_first` is a cautious miss (a tolerated read instead of the intended "
        "write), never a policy violation. `policy_violation` is the dangerous one._\n"
    )
    return "\n".join(lines)
