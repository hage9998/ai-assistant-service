from typing import Protocol


class LLMProvider(Protocol):
    """Contract for LLM providers."""

    async def generate(
        self,
        messages,
        system_prompt: str,
    ) -> str:
        """Generate a response from a list of messages and a system prompt."""
        ...
