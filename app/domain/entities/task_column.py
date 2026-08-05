"""Domain entity representing a task column returned by the MCP service."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskColumn:
    """A column of tasks (e.g. a kanban column) as returned by the MCP service."""

    id: str
    name: str
    tasks: list[dict] = field(default_factory=list)
