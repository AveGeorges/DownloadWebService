import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.infrastructure.logging import configure_logging
from app.presentation.api.router import api_router
from app.presentation.middleware import RequestContextMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    logger.info("API starting", extra={"app_env": settings.app_env})
    try:
        yield
    finally:
        logger.info("API shutting down gracefully")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    application.include_router(api_router)
    return application


app = create_app()
