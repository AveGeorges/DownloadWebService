from celery import Celery

from app.config import get_settings
from app.infrastructure.logging import configure_logging


def create_celery_app() -> Celery:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    celery_app = Celery(
        "download_web_service",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.workers.tasks"],
    )
    celery_app.conf.update(
        task_track_started=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        worker_hijack_root_logger=False,
        worker_redirect_stdouts=False,
        # Soft shutdown: finish current task before exit on SIGTERM (compose stop).
        worker_soft_shutdown_timeout=30,
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry_on_startup=True,
    )
    return celery_app


celery_app = create_celery_app()
