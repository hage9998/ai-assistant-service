"""Domain entity representing a conversation message.

It's the basic unit used to build the message history
sent to the LLMProvider, regardless of the provider (Ollama, OpenAI, etc).
"""

from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Role of the message author within the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    """Message exchanged between the user and the assistant."""

    role: MessageRole
    content: str
