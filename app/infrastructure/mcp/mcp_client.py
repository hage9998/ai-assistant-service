import json
import logging

import httpx2
from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

from app.domain.entities.task_column import TaskColumn
from app.domain.exceptions.domain_exceptions import McpClientException

logger = logging.getLogger(__name__)

_GET_TASK_COLUMNS_TOOL = "get_task_columns"


class McpServiceClient:
    """MCP client that talks to the MCP service over Streamable HTTP."""

    def __init__(self, service_url: str, timeout_seconds: float) -> None:
        self._service_url = service_url
        self._timeout_seconds = timeout_seconds

    async def get_task_columns(self, cookie_header: str) -> list[TaskColumn]:
        """Fetch the user's task columns via the MCP service's get_task_columns tool."""
        try:
            async with httpx2.AsyncClient(
                headers={"Cookie": cookie_header}, timeout=self._timeout_seconds
            ) as http_client:
                async with streamable_http_client(
                    self._service_url, http_client=http_client
                ) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(_GET_TASK_COLUMNS_TOOL)
        except Exception as e:
            logger.exception("Failed to call MCP service")
            raise McpClientException() from e

        if result.is_error:
            logger.error("MCP tool %s returned an error result", _GET_TASK_COLUMNS_TOOL)
            raise McpClientException()

        columns = self._extract_columns(result)
        return [
            TaskColumn(id=column["id"], name=column["name"], tasks=column.get("tasks", []))
            for column in columns
        ]

    def _extract_columns(self, result: types.CallToolResult) -> list[dict]:
        """Extracts the tool's JSON payload, preferring `structured_content`.

        Some MCP protocol versions restrict `structured_content` to a JSON
        object, so a server might return the column list as text content
        instead. Fall back to parsing the first text block in that case.
        """
        if isinstance(result.structured_content, list):
            return result.structured_content

        for block in result.content:
            text = getattr(block, "text", None)
            if text:
                try:
                    parsed = json.loads(text)
                except (TypeError, ValueError):
                    continue
                if isinstance(parsed, list):
                    return parsed

        return []
