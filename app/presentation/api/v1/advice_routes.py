from fastapi import APIRouter, status
from app.application.dto.advice_dto import AdviceRequestDTO
from app.presentation.dependencies.auth import CurrentUserDependency
from app.presentation.dependencies.use_cases.generate_advice import (
    GenerateAdviceUseCaseDependency,
)
from app.presentation.schemas.advice_schema import AdviceResponseSchema
from app.presentation.schemas.error_schema import ErrorResponseSchema

router = APIRouter(prefix="/advice", tags=["Advice"])


@router.get(
    "/daily",
    response_model=AdviceResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate the daily medieval/mythical advice",
    description=(
        "Should be called whenever the user enters the application's "
        "main screen. Returns a short piece of advice (3-4 sentences), "
        "with a medieval/mythical tone, to motivate the user's journey."
    ),
    responses={401: {"model": ErrorResponseSchema}},
)
async def get_daily_advice(
    current_user: CurrentUserDependency,
    use_case: GenerateAdviceUseCaseDependency,
) -> AdviceResponseSchema:
    """Controller: only validates input, delegates to the use case, and serializes output."""
    request_dto = AdviceRequestDTO(user_id=current_user.id)
    result = await use_case.execute(request_dto)

    return AdviceResponseSchema(message=result.message)
