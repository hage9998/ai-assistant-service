from abc import ABC, abstractmethod
from app.domain.entities.advice_log import AdviceLog


class AdviceLogRepository(ABC):
    """Contract for persisting the advice generated for the user."""

    @abstractmethod
    async def save(self, advice_log: AdviceLog) -> AdviceLog:
        """Persist a generated advice."""
        raise NotImplementedError
