from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Gamification of Life - AI-Assistant Service"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/gamification_llm"
    )
    database_echo: bool = False

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://192.168.49.2:30007"]

    # LLM / Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    llm_temperature: float = 0.7

    # MCP
    mcp_service_url: str
    mcp_timeout_seconds: float = 10.0
    mcp_tool_call_max_iterations: int = 2

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Returns the cached instance of the application settings."""
    return Settings()
