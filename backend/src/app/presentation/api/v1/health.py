from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    version: str
    app: str


class ReadyResponse(BaseModel):
    status: str = Field(examples=["ready"])
    checks: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", version=__version__, app=settings.app_name)


@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def ready() -> ReadyResponse:
    """Readiness probe. Dependency checks will be added in later stages."""
    return ReadyResponse(
        status="ready",
        checks={
            "api": "ok",
            "database": "skipped",
            "redis": "skipped",
            "rabbitmq": "skipped",
        },
    )
