from __future__ import annotations

import logging
from uuid import UUID

from app.application.use_cases.run_download_job import RunDownloadJobUseCase
from app.config import get_settings
from app.domain.exceptions import CatalogBlockedError, DownloadJobNotFoundError
from app.infrastructure.db.repositories import (
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.external.factory import build_external_catalog_client
from app.infrastructure.redis.client import build_redis_client
from app.infrastructure.redis.job_lock import RedisDownloadJobLock
from app.infrastructure.redis.progress_store import RedisJobProgressStore
from app.infrastructure.storage.file_storage import FileStorage
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.ping")
def ping() -> str:
    """Smoke-task used to verify Celery worker is alive."""
    return "pong"


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_download_job",
    max_retries=None,
    autoretry_for=(),
    soft_time_limit=60 * 30,
    time_limit=60 * 35,
)
def run_download_job(self, job_id: str) -> dict[str, str | int]:
    settings = get_settings()
    redis_client = build_redis_client(settings)
    lock = RedisDownloadJobLock(redis_client)
    progress_store = RedisJobProgressStore(redis_client)
    storage = FileStorage(settings.files_storage_path)
    catalog = build_external_catalog_client(settings)
    session_factory = get_session_factory()
    job_uuid = UUID(job_id)

    session = session_factory()
    try:
        jobs = SqlAlchemyDownloadJobRepository(session)
        files = SqlAlchemyDownloadedFileRepository(session)

        use_case = RunDownloadJobUseCase(
            jobs=jobs,
            files=files,
            catalog=catalog,
            storage=storage,
            progress_store=progress_store,
            commit=session.commit,
        )

        try:
            lock.refresh(job_uuid)
            job = use_case.execute(job_uuid)
            lock.release(job_uuid)
            return {
                "job_id": str(job.id),
                "status": job.status.value,
                "downloaded_count": job.downloaded_count,
                "names_received": job.names_received,
            }
        except CatalogBlockedError as exc:
            countdown = max(1, int(exc.retry_after_seconds))
            logger.warning(
                "Job %s waiting for catalog unblock, retry in %ss",
                job_id,
                countdown,
            )
            raise self.retry(countdown=countdown, exc=exc) from exc
        except DownloadJobNotFoundError:
            lock.release(job_uuid)
            raise
        except Exception:
            lock.release(job_uuid)
            raise
    finally:
        session.close()
        catalog.close()
        redis_client.close()
