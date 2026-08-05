from fastapi import APIRouter, Request, status
from app.application.dto.prompt_dto import PromptRequestDTO
from app.presentation.dependencies.auth import CurrentUserDependency
from app.presentation.dependencies.use_cases.handle_prompt import (
    HandlePromptUseCaseDependency,
)
from app.presentation.schemas.error_schema import ErrorResponseSchema
from app.presentation.schemas.prompt_schema import PromptRequestSchema, PromptResponseSchema

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post(
    "/prompt",
    response_model=PromptResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Answer a free-form prompt, listing tasks via the MCP service when needed",
    description=(
        "Sends the prompt to the LLM. If the prompt asks about or requires "
        "listing tasks, the LLM calls the MCP service to fetch the user's "
        "task columns before answering."
    ),
    responses={401: {"model": ErrorResponseSchema}},
)
async def handle_prompt(
    request: Request,
    body: PromptRequestSchema,
    current_user: CurrentUserDependency,
    use_case: HandlePromptUseCaseDependency,
) -> PromptResponseSchema:
    """Controller: only validates input, delegates to the use case, and serializes output."""
    request_dto = PromptRequestDTO(prompt=body.prompt)
    cookie_header = request.headers.get("cookie")

    result = await use_case.execute(request_dto, cookie_header)

    return PromptResponseSchema(message=result.message, tasks=result.tasks)
