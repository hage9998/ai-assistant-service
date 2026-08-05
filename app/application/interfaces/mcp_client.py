from typing import Protocol
from app.domain.entities.task_column import TaskColumn


class McpClient(Protocol):
    """Contract for clients that talk to the MCP service."""

    async def get_task_columns(self, cookie_header: str) -> list[TaskColumn]:
        """Fetch the user's task columns via the MCP service's get_task_columns tool."""
        ...
