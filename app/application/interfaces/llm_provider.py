from typing import Protocol
from app.application.dto.tool_calling import ToolCallResult, ToolSpec
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

    async def generate_with_tools(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolSpec],
    ) -> ToolCallResult:
        """Generate a response, letting the model choose to call one of `tools`.

        Returns either the final text (no tool needed) or the name/args of
        the tool the model wants to call.
        """
        ...
