from __future__ import annotations

from uuid import UUID

from app.application.dto.job_progress import JobProgressView
from app.application.ports.progress_store import JobProgressStore
from app.domain.entities import DownloadJob
from app.domain.exceptions import DownloadJobNotFoundError
from app.domain.repositories import DownloadJobRepository


class GetDownloadJobUseCase:
    def __init__(
        self,
        *,
        jobs: DownloadJobRepository,
        progress_store: JobProgressStore,
    ) -> None:
        self._jobs = jobs
        self._progress_store = progress_store

    def execute(self, job_id: UUID) -> tuple[DownloadJob, JobProgressView | None]:
        job = self._jobs.get(job_id)
        if job is None:
            raise DownloadJobNotFoundError(str(job_id))
        progress = self._progress_store.get(job_id)
        return job, progress
