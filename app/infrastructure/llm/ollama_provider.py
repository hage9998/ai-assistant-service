import logging
import time

from langchain_ollama import ChatOllama

from app.application.dto.tool_calling import ToolCallResult, ToolSpec
from app.domain.entities.message import Message
from app.infrastructure.llm.chain_factory import (
    build_chat_chain,
    build_tool_calling_chain,
    to_langchain_messages,
)
from app.infrastructure.observability.instrumentation import get_meter

logger = logging.getLogger(__name__)

_generation_duration_histogram = get_meter().create_histogram(
    "llm_generation_duration_seconds",
    unit="s",
    description="Duration of LLM advice generation calls",
)


def _to_openai_tool(tool: ToolSpec) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


class OllamaProvider:
    """LLM provider based on Ollama."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float = 0.7,
    ) -> None:
        self._llm = ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
        )
        self._chain = build_chat_chain(self._llm)

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str,
    ) -> str:
        """Generate a response from a list of messages and a system prompt."""
        history = to_langchain_messages(
            [(message.role.value, message.content) for message in messages]
        )

        logger.debug(
            "Generating response for %s with %d messages",
            self._llm.model,
            len(history),
        )

        start = time.perf_counter()
        status = "success"
        try:
            result: str = await self._chain.ainvoke(
                {"system_prompt": system_prompt, "history": history}
            )
        except Exception:
            status = "error"
            raise
        finally:
            _generation_duration_histogram.record(
                time.perf_counter() - start, {"status": status}
            )
        return result

    async def generate_with_tools(
        self,
        messages: list[Message],
        system_prompt: str,
        tools: list[ToolSpec],
    ) -> ToolCallResult:
        """Generate a response, letting the model choose to call one of `tools`."""
        history = to_langchain_messages(
            [(message.role.value, message.content) for message in messages]
        )
        chain = build_tool_calling_chain(self._llm, [_to_openai_tool(tool) for tool in tools])

        logger.debug(
            "Generating tool-calling response for %s with %d messages and %d tools",
            self._llm.model,
            len(history),
            len(tools),
        )

        start = time.perf_counter()
        status = "success"
        try:
            ai_message = await chain.ainvoke(
                {"system_prompt": system_prompt, "history": history}
            )
        except Exception:
            status = "error"
            raise
        finally:
            _generation_duration_histogram.record(
                time.perf_counter() - start, {"status": status}
            )

        if ai_message.tool_calls:
            call = ai_message.tool_calls[0]
            return ToolCallResult(tool_name=call["name"], tool_args=call.get("args") or {})
        return ToolCallResult(text=ai_message.content)
