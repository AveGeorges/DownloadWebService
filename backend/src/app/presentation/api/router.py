from fastapi import APIRouter

from app.presentation.api.v1.health import router as health_router
from app.presentation.api.v1.router import router as v1_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router, prefix="/api/v1")
