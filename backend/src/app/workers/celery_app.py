from celery import Celery

from app.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    celery_app = Celery(
        "download_web_service",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.workers.tasks"],
    )
    celery_app.conf.update(
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        timezone="UTC",
        enable_utc=True,
    )
    return celery_app


celery_app = create_celery_app()
