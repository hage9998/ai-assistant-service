from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.advice_log import AdviceLog
from app.domain.repositories.advice_log_repository import AdviceLogRepository
from app.infrastructure.orm.models import AdviceLogModel


class SqlAlchemyAdviceLogRepository(AdviceLogRepository):
    """Persists the advice generated for the user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, advice_log: AdviceLog) -> AdviceLog:
        model = AdviceLogModel(
            id=advice_log.id,
            user_id=advice_log.user_id,
            advice=advice_log.advice,
            created_at=advice_log.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return advice_log
