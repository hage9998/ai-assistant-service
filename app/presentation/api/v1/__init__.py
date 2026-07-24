from fastapi import APIRouter

from app.presentation.api.v1.advice_routes import router as advice_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(advice_router)
