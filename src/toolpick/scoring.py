"""Deterministic scoring for a single tool-selection attempt.

Four sub-scores, each in [0, 1]:

* tool_selection    - did the model pick the policy-correct tool?
* parameter_accuracy- of the expected argument constraints, what fraction hold?
                      (only meaningful when the tool is right; 0 otherwise)
* policy_adherence  - did the model avoid a tool that is forbidden for this task?
                      (e.g. issuing a refund before checking eligibility)
* correct           - the honest headline: 1.0 only when the tool is right, in
                      policy, and every required argument is present.

There is no LLM judge here. Tool selection has a known-correct answer, so it is
scored deterministically, which is cheaper, reproducible, and immune to judge bias.
"""

from __future__ import annotations

from .types import Scores, Task, ToolCall


def _parameter_accuracy(task: Task, call: ToolCall) -> tuple[float, bool]:
    """Return (fraction satisfied, all_required_present)."""
    if not task.expected_args:
        return 1.0, True
    satisfied = 0
    all_present = True
    for name, constraint in task.expected_args.items():
        present = name in call.arguments
        if not present:
            all_present = False
            continue
        ok = True
        if "equals" in constraint:
            ok = str(call.arguments.get(name)) == str(constraint["equals"])
        if ok:
            satisfied += 1
        else:
            all_present = False
    return satisfied / len(task.expected_args), all_present


def score(task: Task, call: ToolCall | None) -> Scores:
    """Score one attempt against one task."""
    if call is None:
        return Scores(0.0, 0.0, 1.0, 0.0)  # declining is in-policy but never correct

    policy = 0.0 if call.tool in task.forbidden_tools else 1.0
    tool_ok = 1.0 if call.tool == task.expected_tool else 0.0

    if tool_ok:
        param_frac, all_required = _parameter_accuracy(task, call)
    else:
        param_frac, all_required = 0.0, False

    correct = 1.0 if (tool_ok == 1.0 and policy == 1.0 and all_required) else 0.0
    return Scores(
        tool_selection=tool_ok,
        parameter_accuracy=param_frac,
        policy_adherence=policy,
        correct=correct,
    )
