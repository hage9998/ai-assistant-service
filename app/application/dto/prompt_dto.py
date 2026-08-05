"""Input/output DTOs for the prompt handling use case."""

from dataclasses import dataclass

from app.domain.entities.task_column import TaskColumn


@dataclass(frozen=True)
class PromptRequestDTO:
    """Input of the prompt handling use case."""

    prompt: str


@dataclass(frozen=True)
class PromptResponseDTO:
    """Output of the prompt handling use case."""

    message: str
    tasks: list[TaskColumn] | None = None
