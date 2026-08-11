"""Run the benchmark against any real model via LiteLLM.

LiteLLM gives one interface to OpenAI, Anthropic, Google, open models via
OpenRouter, a local vLLM/Ollama endpoint, and so on. Install the extra and set the
provider's key:

    pip install "toolpick[litellm]"
    export OPENAI_API_KEY=...        # or ANTHROPIC_API_KEY, OPENROUTER_API_KEY, ...
    toolpick run --provider litellm --model gpt-4o-mini
"""

from __future__ import annotations

import json

from ..types import Tool, ToolCall
from .base import DEFAULT_SYSTEM


class LiteLLMProvider:
    name = "litellm"

    def __init__(self, model: str, temperature: float = 0.0, **kwargs) -> None:
        try:
            import litellm  # noqa: F401
        except ImportError as e:  # pragma: no cover - exercised only without the extra
            raise ImportError(
                "The litellm provider needs the extra: pip install 'toolpick[litellm]'"
            ) from e
        self.model = model
        self.temperature = temperature
        self._kwargs = kwargs

    def select_tool(self, system: str, request: str, tools: list[Tool]) -> ToolCall | None:
        import litellm

        resp = litellm.completion(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system or DEFAULT_SYSTEM},
                {"role": "user", "content": request},
            ],
            tools=[t.to_openai() for t in tools],
            tool_choice="required",
            **self._kwargs,
        )
        message = resp.choices[0].message
        calls = getattr(message, "tool_calls", None)
        if not calls:
            return None
        call = calls[0]
        raw = call.function.arguments or "{}"
        try:
            args = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (json.JSONDecodeError, TypeError):
            args = {}
        return ToolCall(tool=call.function.name, arguments=args)
