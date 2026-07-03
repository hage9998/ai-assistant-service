from typing import Protocol
from app.domain.entities.message import Message


class LLMProvider(Protocol):
    """Contract for LLM providers."""

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str,
    ) -> str:
        """Generate a response from a list of messages and a system prompt."""
        ...
