from fastapi import APIRouter, status

from app.presentation.dependencies.auth import CurrentUserDependency
from app.presentation.dependencies.use_cases.generate_advice import (
    GenerateAdviceUseCaseDependency,
)

router = APIRouter(prefix="/advice", tags=["Advice"])


@router.get(
    "/daily",
    status_code=status.HTTP_200_OK,
    summary="Generate the daily medieval/mythical advice",
    description=(
        "Should be called whenever the user enters the application's "
        "main screen. Returns a short piece of advice (3-4 sentences), "
        "with a medieval/mythical tone, to motivate the user's journey."
    ),
)
async def get_daily_advice(
    current_user: CurrentUserDependency,
    use_case: GenerateAdviceUseCaseDependency,
):
    """Controller: only validates input, delegates to the use case, and serializes output."""
