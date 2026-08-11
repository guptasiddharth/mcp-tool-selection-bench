"""Provider registry and factory."""

from __future__ import annotations

from .base import DEFAULT_SYSTEM, Provider
from .mock import MockProvider

__all__ = ["DEFAULT_SYSTEM", "MockProvider", "Provider", "get_provider"]


def get_provider(name: str, model: str | None = None, seed: int = 0, **kwargs) -> Provider:
    """Build a provider by name. ``mock`` is dependency-free; ``litellm`` needs the extra."""
    if name == "mock":
        return MockProvider(seed=seed, model=model or "keyword-heuristic-v1")
    if name == "litellm":
        from .litellm_provider import LiteLLMProvider

        if not model:
            raise ValueError("The litellm provider requires --model (e.g. gpt-4o-mini).")
        return LiteLLMProvider(model=model, **kwargs)
    raise ValueError(f"Unknown provider: {name!r}. Known: mock, litellm.")
