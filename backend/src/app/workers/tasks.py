from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.ping")
def ping() -> str:
    """Smoke-task used to verify Celery worker is alive."""
    return "pong"
