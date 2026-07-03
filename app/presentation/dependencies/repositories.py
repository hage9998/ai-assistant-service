from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.advice_log_repository import AdviceLogRepository
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.advice_log_repository_impl import (
    SqlAlchemyAdviceLogRepository,
)


def get_advice_log_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdviceLogRepository:
    """Provides the advice log repository."""
    return SqlAlchemyAdviceLogRepository(session)


AdviceLogRepositoryDependency = Annotated[
    AdviceLogRepository, Depends(get_advice_log_repository)
]
