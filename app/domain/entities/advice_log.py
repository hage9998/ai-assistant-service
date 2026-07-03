"""Domain entity representing the log of a medieval/mythical advice
generated for the user when entering the main screen.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class AdviceLog:
    """Log of an advice generated for the user."""

    user_id: str
    advice: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
