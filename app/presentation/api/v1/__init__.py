from fastapi import APIRouter

from app.presentation.api.v1.advice_routes import router as advice_router
from app.presentation.api.v1.prompt_routes import router as prompt_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(advice_router)
api_v1_router.include_router(prompt_router)
