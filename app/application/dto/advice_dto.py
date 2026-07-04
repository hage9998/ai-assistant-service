"""Input/output DTOs for the advice generation use case."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AdviceRequestDTO:
    """Input of the advice generation use case."""

    user_id: str


@dataclass(frozen=True)
class AdviceResponseDTO:
    """Output of the advice generation use case."""

    message: str
