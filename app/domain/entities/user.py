from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    """Represents the authenticated user."""

    id: str
    email: str
    name: str
