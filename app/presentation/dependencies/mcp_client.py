from functools import lru_cache

from app.application.interfaces.mcp_client import McpClient
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.mcp.mcp_client import McpServiceClient


@lru_cache
def get_mcp_client() -> McpClient:
    """Provides a singleton instance of the McpClient."""
    settings: Settings = get_settings()
    return McpServiceClient(
        service_url=settings.mcp_service_url,
        timeout_seconds=settings.mcp_timeout_seconds,
    )
