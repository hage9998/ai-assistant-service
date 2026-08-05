from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    """Describes a tool the LLM may choose to call."""

    name: str
    description: str
    parameters: dict = field(default_factory=lambda: {"type": "object", "properties": {}})


@dataclass(frozen=True)
class ToolCallResult:
    """Result of asking the LLM to generate a response with tools available.

    Either `text` is set (the LLM answered directly, no tool needed) or
    `tool_name` is set (the LLM wants to call that tool before answering).
    """

    text: str | None = None
    tool_name: str | None = None
    tool_args: dict = field(default_factory=dict)

    @property
    def requires_tool_call(self) -> bool:
        return self.tool_name is not None
