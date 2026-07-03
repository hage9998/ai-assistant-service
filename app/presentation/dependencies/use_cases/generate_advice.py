"""Fábrica de Dependency Injection do `GenerateAdviceUseCase`."""

from typing import Annotated

from fastapi import Depends

from app.application.interfaces.llm_provider import LLMProvider
from app.application.use_cases.generate_advice import GenerateAdviceUseCase
from app.presentation.dependencies.llm_provider import get_llm_provider
from app.presentation.dependencies.repositories import AdviceLogRepositoryDependency


def get_generate_advice_use_case(
    llm_provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    advice_log_repository: AdviceLogRepositoryDependency,
) -> GenerateAdviceUseCase:
    """Provides a singleton instance of the GenerateAdviceUseCase."""
    return GenerateAdviceUseCase(
        llm_provider=llm_provider,
        advice_log_repository=advice_log_repository,
    )


GenerateAdviceUseCaseDependency = Annotated[
    GenerateAdviceUseCase, Depends(get_generate_advice_use_case)
]
