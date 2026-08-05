"""Pydantic (request/response) schemas for the assistant prompt endpoint."""

from pydantic import BaseModel, Field, field_validator


class PromptRequestSchema(BaseModel):
    """Request body for the `POST /assistant/prompt` endpoint."""

    prompt: str = Field(
        ...,
        min_length=1,
        examples=["Quais tarefas eu tenho pra hoje?"],
    )

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be blank")
        return stripped


class TaskColumnSchema(BaseModel):
    """A column of tasks, as returned by the MCP service."""

    id: str
    name: str
    tasks: list[dict] = Field(default_factory=list)


class PromptResponseSchema(BaseModel):
    """Response body for the `POST /assistant/prompt` endpoint."""

    message: str = Field(
        ...,
        description="Medieval/mythical response to the user's prompt.",
    )
    tasks: list[TaskColumnSchema] | None = Field(
        default=None,
        description="Task columns fetched from the MCP service, when requested.",
    )
