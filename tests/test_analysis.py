"""Every miss taxonomy category, with results scored exactly as the runner does."""

from __future__ import annotations

from toolpick import analysis
from toolpick.analysis import CATEGORIES, _is_read_first, classify
from toolpick.scoring import score
from toolpick.types import RunResult, Scores, Task, TaskResult, ToolCall

# A task whose correct first move is a write (reply), with a read it tolerates
# (get_ticket) and a forbidden move (close before resolved).
WRITE_TASK = Task(
    id="sup-1",
    domain="support",
    prompt="Reply to ticket TCK-1 with an update.",
    expected_tool="reply_to_ticket",
    expected_args={"ticket_id": {"equals": "TCK-1"}},
    acceptable_tools=("get_ticket",),
    forbidden_tools=("close_ticket",),
)

# A task whose correct first move is itself a read (an eligibility check).
READ_TASK = Task(
    id="pay-1",
    domain="payments",
    prompt="Customer wants a refund on TXN-1.",
    expected_tool="check_refund_eligibility",
    expected_args={"transaction_id": {"equals": "TXN-1"}},
    forbidden_tools=("refund_payment",),
)

TASKS = {WRITE_TASK.id: WRITE_TASK, READ_TASK.id: READ_TASK}


def _result(task: Task, call: ToolCall | None, *, error: str | None = None) -> TaskResult:
    """Build a TaskResult exactly the way runner._run_one does (real scoring)."""
    return TaskResult(
        task_id=task.id,
        domain=task.domain,
        difficulty=task.difficulty,
        tags=task.tags,
        call=call,
        scores=score(task, call),
        latency_ms=0.0,
        error=error,
    )


# (label, TaskResult, expected category) -- one case per category, plus extras.
CASES: list[tuple[str, TaskResult, str]] = [
    ("right tool + args", _result(WRITE_TASK, ToolCall("reply_to_ticket", {"ticket_id": "TCK-1"})), "correct"),
    ("forbidden tool", _result(WRITE_TASK, ToolCall("close_ticket", {"ticket_id": "TCK-1"})), "policy_violation"),
    ("right tool, missing arg", _result(WRITE_TASK, ToolCall("reply_to_ticket", {})), "param_error"),
    ("right tool, wrong arg value", _result(WRITE_TASK, ToolCall("reply_to_ticket", {"ticket_id": "TCK-9"})), "param_error"),
    ("read-only instead of write", _result(WRITE_TASK, ToolCall("search_tickets", {"query": "TCK-1"})), "read_first"),
    ("wrong write tool", _result(WRITE_TASK, ToolCall("escalate_ticket", {"ticket_id": "TCK-1"})), "wrong_tool"),
    ("wrong read when a read was expected", _result(READ_TASK, ToolCall("get_transaction", {"transaction_id": "TXN-1"})), "wrong_tool"),
    ("no call", _result(WRITE_TASK, None), "no_call"),
    ("errored attempt", _result(WRITE_TASK, ToolCall("reply_to_ticket", {"ticket_id": "TCK-1"}), error="TimeoutError: boom"), "no_call"),
]


def test_each_case_lands_in_expected_category():
    for label, result, expected in CASES:
        assert classify(result, TASKS[result.task_id]) == expected, label


def test_every_category_is_covered():
    produced = {classify(r, TASKS[r.task_id]) for _, r, _ in CASES}
    assert produced == set(CATEGORIES)


def test_classification_is_total_and_valid():
    for _, result, _ in CASES:
        assert classify(result, TASKS[result.task_id]) in CATEGORIES


def test_error_wins_even_when_the_call_would_score_correct():
    # The errored case has a call that scores correct, yet it must be no_call.
    _, result, _ = CASES[-1]
    assert result.scores.correct == 1.0
    assert classify(result, WRITE_TASK) == "no_call"


def test_acceptable_read_is_read_first_at_the_predicate_level():
    # Under real scoring an acceptable tool scores correct, so classify() routes it
    # to "correct"; the acceptable clause of the predicate is exercised directly.
    r = _result(WRITE_TASK, ToolCall("get_ticket", {"ticket_id": "TCK-1"}))
    assert _is_read_first(r, WRITE_TASK) is True
    assert classify(r, WRITE_TASK) == "correct"


def test_read_picked_when_read_expected_is_not_read_first():
    r = _result(READ_TASK, ToolCall("get_transaction", {"transaction_id": "TXN-1"}))
    assert _is_read_first(r, READ_TASK) is False


def _run(model: str, results: list[TaskResult]) -> RunResult:
    return RunResult(
        provider="mock",
        model=model,
        seed=0,
        suite="core",
        created_at="2026-01-01T00:00:00+00:00",
        results=tuple(results),
    )


def test_counts_are_zero_filled_and_sum_to_n():
    results = [r for _, r, _ in CASES]
    run = _run("m", results)
    counts = analysis.counts_for_run(run, TASKS)
    assert set(counts) == set(CATEGORIES)  # every category key present
    assert sum(counts.values()) == len(results)
    # Two param_error cases, two wrong_tool cases, two no_call cases in CASES.
    assert counts["correct"] == 1
    assert counts["policy_violation"] == 1
    assert counts["param_error"] == 2
    assert counts["read_first"] == 1
    assert counts["wrong_tool"] == 2
    assert counts["no_call"] == 2


def test_counts_by_model_keys_on_model():
    run = _run("model-x", [r for _, r, _ in CASES])
    by_model = analysis.counts_by_model([run], TASKS)
    assert set(by_model) == {"model-x"}
    assert by_model["model-x"]["policy_violation"] == 1


def test_markdown_has_a_row_per_run_and_all_labels():
    runs = [_run("model-a", [r for _, r, _ in CASES])]
    md = analysis.markdown(runs, TASKS)
    assert "ToolPick miss taxonomy" in md
    assert "`model-a`" in md
    assert "Policy violation" in md and "Read first" in md
    assert "_No runs._" in analysis.markdown([], TASKS)


def test_task_index_round_trips():
    idx = analysis.task_index((WRITE_TASK, READ_TASK))
    assert idx[WRITE_TASK.id] is WRITE_TASK


def test_scores_dataclass_is_untouched():
    # Guardrail: classify reads Scores, never constructs or mutates them.
    s = Scores(tool_selection=1.0, parameter_accuracy=0.0, policy_adherence=1.0, correct=0.0)
    r = TaskResult("sup-1", "support", "medium", (), ToolCall("reply_to_ticket", {}), s, 0.0)
    assert classify(r, WRITE_TASK) == "param_error"
