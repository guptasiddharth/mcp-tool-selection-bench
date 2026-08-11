from toolpick.scoring import score
from toolpick.types import Task, ToolCall

TASK = Task(
    id="t1",
    domain="payments",
    prompt="Start the refund on TXN-1.",
    expected_tool="check_refund_eligibility",
    expected_args={"transaction_id": {"equals": "TXN-1"}},
    forbidden_tools=("refund_payment",),
)


def test_correct_choice_scores_one():
    s = score(TASK, ToolCall("check_refund_eligibility", {"transaction_id": "TXN-1"}))
    assert s.tool_selection == 1.0
    assert s.parameter_accuracy == 1.0
    assert s.policy_adherence == 1.0
    assert s.correct == 1.0


def test_wrong_tool_is_incorrect():
    s = score(TASK, ToolCall("get_transaction", {"transaction_id": "TXN-1"}))
    assert s.tool_selection == 0.0
    assert s.parameter_accuracy == 0.0
    assert s.correct == 0.0


def test_forbidden_tool_fails_policy():
    s = score(TASK, ToolCall("refund_payment", {"transaction_id": "TXN-1"}))
    assert s.policy_adherence == 0.0
    assert s.correct == 0.0


def test_right_tool_wrong_arg_value():
    s = score(TASK, ToolCall("check_refund_eligibility", {"transaction_id": "TXN-9"}))
    assert s.tool_selection == 1.0
    assert s.parameter_accuracy == 0.0
    assert s.correct == 0.0  # required arg present but value mismatched


def test_missing_required_arg():
    s = score(TASK, ToolCall("check_refund_eligibility", {}))
    assert s.tool_selection == 1.0
    assert s.parameter_accuracy == 0.0
    assert s.correct == 0.0


def test_declining_is_in_policy_but_not_correct():
    s = score(TASK, None)
    assert s.policy_adherence == 1.0
    assert s.correct == 0.0
