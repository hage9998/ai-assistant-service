from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable


def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
        ]
    )


def build_chat_chain(llm: BaseChatModel) -> Runnable:
    """Builds the default chain: system prompt + history -> model -> text.

    The chain receives a dict in the format `{"history": list[BaseMessage]}`
    and returns a `str` with the model's response.
    """
    return _build_prompt() | llm | StrOutputParser()


def build_tool_calling_chain(llm: BaseChatModel, tools: list[dict]) -> Runnable[dict, AIMessage]:
    """Builds a chain like `build_chat_chain`, but with tools bound to the model.

    Returns the raw `AIMessage` (not just text) so the caller can inspect
    `tool_calls` to decide whether the model wants to call a tool.
    """
    return _build_prompt() | llm.bind_tools(tools)


def to_langchain_messages(
    role_content_pairs: list[tuple[str, str]],
) -> list[BaseMessage]:
    """Converts a list of (role, content) tuples to a list of LangChain messages.

    Kept here (and not in the provider) so that other LangChain-based
    providers can reuse the same conversion logic.
    """
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    mapping = {
        "user": HumanMessage,
        "assistant": AIMessage,
        "system": SystemMessage,
    }
    return [mapping[role](content=content) for role, content in role_content_pairs]
