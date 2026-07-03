import logging

from langchain_ollama import ChatOllama

from app.domain.entities.message import Message
from app.infrastructure.llm.chain_factory import build_chat_chain, to_langchain_messages

logger = logging.getLogger(__name__)


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

        result: str = await self._chain.ainvoke(
            {"system_prompt": system_prompt, "history": history}
        )
        return result
