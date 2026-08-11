"""A deterministic, keyword-heuristic provider.

This exists for two reasons: it lets the whole benchmark run in CI with no API
keys, and it is an honest weak baseline. It scores tool choices by lexical overlap
between the request and each tool's name and description, with a seeded tie-break,
so it is reproducible and gets the distractor and policy tasks wrong in exactly the
way a naive keyword matcher would. If a real model cannot beat this, that is a
finding, not a bug.
"""

from __future__ import annotations

import random
import re

from ..types import Tool, ToolCall

_ID_RE = re.compile(r"\b([A-Za-z]{0,4}[-_]?\d{3,})\b")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


class MockProvider:
    name = "mock"

    def __init__(self, seed: int = 0, model: str = "keyword-heuristic-v1") -> None:
        self.model = model
        self._rng = random.Random(seed)

    def select_tool(self, system: str, request: str, tools: list[Tool]) -> ToolCall | None:
        req = _tokens(request)
        best_score = -1.0
        best: list[Tool] = []
        for t in tools:
            name_toks = _tokens(t.name.replace("_", " "))
            desc_toks = _tokens(t.description)
            # Name matches count double; description matches are weaker signal.
            score = 2.0 * len(req & name_toks) + 1.0 * len(req & desc_toks)
            if score > best_score:
                best_score, best = score, [t]
            elif score == best_score:
                best.append(t)
        if not best:
            return None
        chosen = self._rng.choice(best)
        args = self._guess_args(chosen, request)
        return ToolCall(tool=chosen.name, arguments=args)

    def _guess_args(self, tool: Tool, request: str) -> dict:
        """Fill required string params with the first id-like token, naively."""
        props = (tool.parameters or {}).get("properties", {}) or {}
        required = (tool.parameters or {}).get("required", []) or []
        args: dict = {}
        m = _ID_RE.search(request)
        ident = m.group(1) if m else None
        for key in required:
            spec = props.get(key, {})
            if spec.get("type") == "string" and ident:
                args[key] = ident
        return args
