from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app import __version__
from app.config import get_settings
from app.infrastructure.db.session import check_database

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


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response) -> ReadyResponse:
    checks = {
        "api": "ok",
        "database": "ok",
        "redis": "skipped",
        "rabbitmq": "skipped",
    }

    try:
        check_database()
    except Exception:
        checks["database"] = "fail"

    if checks["database"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="not_ready", checks=checks)

    return ReadyResponse(status="ready", checks=checks)
