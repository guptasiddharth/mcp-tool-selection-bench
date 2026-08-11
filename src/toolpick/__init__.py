"""ToolPick: an open, contamination-aware benchmark for MCP tool selection.

Public API::

    from toolpick import load_suite, get_provider, run, markdown, summarize
"""

from __future__ import annotations

__version__ = "0.1.0"

from .providers import get_provider
from .report import markdown, summarize
from .runner import run
from .suites.loader import load_suite

__all__ = ["__version__", "get_provider", "load_suite", "markdown", "run", "summarize"]
