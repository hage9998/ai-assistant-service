from typing import Annotated
from fastapi import Depends
from app.application.interfaces.llm_provider import LLMProvider
from app.application.interfaces.mcp_client import McpClient
from app.application.use_cases.handle_prompt import HandlePromptUseCase
from app.infrastructure.config.settings import Settings, get_settings
from app.presentation.dependencies.llm_provider import get_llm_provider
from app.presentation.dependencies.mcp_client import get_mcp_client


def get_handle_prompt_use_case(
    llm_provider: Annotated[LLMProvider, Depends(get_llm_provider)],
    mcp_client: Annotated[McpClient, Depends(get_mcp_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HandlePromptUseCase:
    """Provides a singleton instance of the HandlePromptUseCase."""
    return HandlePromptUseCase(
        llm_provider=llm_provider,
        mcp_client=mcp_client,
        max_tool_iterations=settings.mcp_tool_call_max_iterations,
    )


HandlePromptUseCaseDependency = Annotated[
    HandlePromptUseCase, Depends(get_handle_prompt_use_case)
]
