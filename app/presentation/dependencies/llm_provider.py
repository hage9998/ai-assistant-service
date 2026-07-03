from functools import lru_cache

from app.application.interfaces.llm_provider import LLMProvider
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.llm.ollama_provider import OllamaProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Provides a singleton instance of the LLMProvider."""
    settings: Settings = get_settings()
    return OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.llm_temperature,
    )
