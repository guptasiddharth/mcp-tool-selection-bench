"""Load servers and tasks from disk and assemble the tools each task can see."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..types import Server, Task, Tool


def default_data_dir() -> Path:
    """Find the data directory: $TOOLPICK_DATA, then a `data/servers` up the tree,
    then the repo-relative fallback next to the installed package."""
    env = os.environ.get("TOOLPICK_DATA")
    if env:
        return Path(env)
    here = Path.cwd()
    for base in [here, *here.parents]:
        if (base / "data" / "servers").is_dir():
            return base / "data"
    # Fallback for an editable/repo install: src/toolpick/suites/ -> repo/data
    return Path(__file__).resolve().parents[3] / "data"


@dataclass(frozen=True)
class Suite:
    name: str
    servers: dict[str, Server]
    tasks: tuple[Task, ...]

    def tools_for(self, task: Task, *, cross_domain: bool = False) -> list[Tool]:
        """Tools the agent sees for a task. By default, the task's own domain
        server (which already contains overlapping, distractor tools). With
        cross_domain, every server's tools are visible, which is harder."""
        if cross_domain:
            out: list[Tool] = []
            for s in self.servers.values():
                out.extend(s.tools)
            return out
        return list(self.servers[task.domain].tools)

    @property
    def domains(self) -> list[str]:
        return sorted(self.servers)


def load_suite(data_dir: Path | None = None, name: str = "core") -> Suite:
    data_dir = Path(data_dir) if data_dir else default_data_dir()
    servers: dict[str, Server] = {}
    for p in sorted((data_dir / "servers").glob("*.json")):
        s = Server.from_json(p)
        servers[p.stem] = s
    tasks: list[Task] = []
    for p in sorted((data_dir / "tasks").glob("*.jsonl")):
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tasks.append(Task.from_dict(json.loads(line)))
    if not servers:
        raise FileNotFoundError(f"No servers found under {data_dir/'servers'}")
    if not tasks:
        raise FileNotFoundError(f"No tasks found under {data_dir/'tasks'}")
    # Validate every task's expected/forbidden tools exist in its domain server.
    for t in tasks:
        if t.domain not in servers:
            raise ValueError(f"Task {t.id}: unknown domain {t.domain!r}")
        names = {tool.name for tool in servers[t.domain].tools}
        if t.expected_tool not in names:
            raise ValueError(f"Task {t.id}: expected_tool {t.expected_tool!r} not in {t.domain}")
        for f in t.forbidden_tools:
            if f not in names:
                raise ValueError(f"Task {t.id}: forbidden tool {f!r} not in {t.domain}")
    return Suite(name=name, servers=servers, tasks=tuple(tasks))
