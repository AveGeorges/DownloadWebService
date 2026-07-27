from __future__ import annotations

import logging
from collections.abc import Callable

from app.application.dto.job_progress import JobProgressView
from app.application.ports.job_lock import DownloadJobLock
from app.application.ports.progress_store import JobProgressStore
from app.application.ports.task_enqueuer import DownloadJobEnqueuer
from app.domain.entities import DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import ActiveDownloadExistsError
from app.domain.repositories import DownloadJobRepository

logger = logging.getLogger(__name__)


class StartDownloadJobUseCase:
    """Create a download job, take the global lock, and enqueue Celery work."""

    def __init__(
        self,
        *,
        jobs: DownloadJobRepository,
        lock: DownloadJobLock,
        progress_store: JobProgressStore,
        enqueuer: DownloadJobEnqueuer,
        commit: Callable[[], None],
        lock_ttl_seconds: int = 3600,
    ) -> None:
        self._jobs = jobs
        self._lock = lock
        self._progress_store = progress_store
        self._enqueuer = enqueuer
        self._commit = commit
        self._lock_ttl_seconds = lock_ttl_seconds

    def execute(self) -> DownloadJob:
        holder = self._lock.get_holder()
        if holder is not None:
            raise ActiveDownloadExistsError(f"Active download job already running: {holder}")

        job = DownloadJob(status=DownloadJobStatus.PENDING)
        if not self._lock.acquire(job.id, ttl_seconds=self._lock_ttl_seconds):
            holder = self._lock.get_holder()
            raise ActiveDownloadExistsError(
                f"Active download job already running: {holder or 'unknown'}"
            )

        try:
            saved = self._jobs.add(job)
            self._commit()
            self._progress_store.save(
                JobProgressView(
                    job_id=str(saved.id),
                    status=saved.status.value,
                    names_received=saved.names_received,
                    downloaded_count=saved.downloaded_count,
                    started_at=saved.started_at.isoformat(),
                    error=saved.error,
                )
            )
            self._enqueuer.enqueue_run_download_job(saved.id)
            logger.info("Enqueued download job %s", saved.id)
            return saved
        except Exception:
            self._lock.release(job.id)
            raise
