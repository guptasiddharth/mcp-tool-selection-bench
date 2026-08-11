"""Core data types for the ToolPick MCP tool-selection benchmark.

The unit of work is a *task*: a natural-language request plus the set of tools an
agent can see. The agent must choose the single correct first tool call under the
domain's policy. Everything downstream (scoring, statistics, reporting) is derived
from the immutable record of what each model chose, so a decision rule can change
without re-running any model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Tool:
    """A single tool an agent may call, as an MCP server would advertise it."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the arguments

    def to_openai(self) -> dict[str, Any]:
        """Render as an OpenAI/LiteLLM function-tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class Server:
    """A named group of tools, standing in for one MCP server."""

    name: str
    tools: tuple[Tool, ...]

    @staticmethod
    def from_json(path: Path) -> Server:
        data = json.loads(Path(path).read_text())
        tools = tuple(
            Tool(t["name"], t["description"], t.get("parameters", {"type": "object", "properties": {}}))
            for t in data["tools"]
        )
        return Server(name=data["name"], tools=tools)


@dataclass(frozen=True)
class Task:
    """One graded item: a request, its policy-correct tool, and how to score it."""

    id: str
    domain: str
    prompt: str
    expected_tool: str
    # arg-name -> constraint. Presence is always required; {"equals": v} also
    # checks the value. Extra constraints are ignored so data stays forward-safe.
    expected_args: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Other first moves that are also correct for this task, typically a read or
    # inspect before acting (e.g. get_ticket before reply_to_ticket). Choosing one
    # counts as a right tool but is not held to the expected_args of the main tool.
    acceptable_tools: tuple[str, ...] = ()
    # tools that are tempting but violate policy for this task (e.g. issuing a
    # refund before checking eligibility). Choosing one is a policy violation.
    forbidden_tools: tuple[str, ...] = ()
    difficulty: str = "medium"
    tags: tuple[str, ...] = ()
    rationale: str = ""

    def accepted(self) -> set[str]:
        """The expected tool plus any explicitly acceptable alternatives."""
        return {self.expected_tool, *self.acceptable_tools}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Task:
        return Task(
            id=d["id"],
            domain=d["domain"],
            prompt=d["prompt"],
            expected_tool=d["expected_tool"],
            expected_args={k: dict(v) for k, v in d.get("expected_args", {}).items()},
            acceptable_tools=tuple(d.get("acceptable_tools", [])),
            forbidden_tools=tuple(d.get("forbidden_tools", [])),
            difficulty=d.get("difficulty", "medium"),
            tags=tuple(d.get("tags", [])),
            rationale=d.get("rationale", ""),
        )


@dataclass(frozen=True)
class ToolCall:
    """A model's choice: which tool, with which arguments."""

    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Scores:
    """Per-task sub-scores. See scoring.py for definitions."""

    tool_selection: float
    parameter_accuracy: float
    policy_adherence: float
    correct: float  # 1.0 only if the whole choice is right and in-policy


@dataclass(frozen=True)
class TaskResult:
    """The immutable record of one model attempting one task."""

    task_id: str
    domain: str
    difficulty: str
    tags: tuple[str, ...]
    call: ToolCall | None
    scores: Scores
    latency_ms: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain,
            "difficulty": self.difficulty,
            "tags": list(self.tags),
            "call": None if self.call is None else {"tool": self.call.tool, "arguments": self.call.arguments},
            "scores": {
                "tool_selection": self.scores.tool_selection,
                "parameter_accuracy": self.scores.parameter_accuracy,
                "policy_adherence": self.scores.policy_adherence,
                "correct": self.scores.correct,
            },
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


@dataclass(frozen=True)
class RunResult:
    """A whole run of one provider over one suite."""

    provider: str
    model: str
    seed: int
    suite: str
    created_at: str
    results: tuple[TaskResult, ...]
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "seed": self.seed,
            "suite": self.suite,
            "created_at": self.created_at,
            "meta": self.meta,
            "results": [r.to_dict() for r in self.results],
        }
