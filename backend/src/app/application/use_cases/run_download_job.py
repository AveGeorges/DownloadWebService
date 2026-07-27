from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from app.application.dto.job_progress import JobProgressView
from app.application.ports.external_catalog import ExternalCatalogPort
from app.application.ports.progress_store import JobProgressStore
from app.application.services.chunking import chunked
from app.domain.entities import DownloadedFile, DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import CatalogBlockedError, DownloadJobNotFoundError
from app.domain.filename import sanitize_filename
from app.domain.repositories import DownloadedFileRepository, DownloadJobRepository
from app.infrastructure.storage.file_storage import FileStorage
from app.infrastructure.zip.extractor import extract_zip_files

logger = logging.getLogger(__name__)


class RunDownloadJobUseCase:
    """Download the full external catalog for a single job."""

    def __init__(
        self,
        *,
        jobs: DownloadJobRepository,
        files: DownloadedFileRepository,
        catalog: ExternalCatalogPort,
        storage: FileStorage,
        progress_store: JobProgressStore,
        commit: Callable[[], None],
    ) -> None:
        self._jobs = jobs
        self._files = files
        self._catalog = catalog
        self._storage = storage
        self._progress_store = progress_store
        self._commit = commit

    def execute(self, job_id: UUID) -> DownloadJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise DownloadJobNotFoundError(str(job_id))

        job.status = DownloadJobStatus.RUNNING
        job.error = None
        self._persist(job)

        try:
            while True:
                names = self._catalog.list_names()
                if not names:
                    break

                job.names_received += len(names)
                self._persist(job)

                for batch in chunked(names):
                    self._process_batch(job, batch)

            job.status = DownloadJobStatus.COMPLETED
            job.finished_at = datetime.now(UTC)
            job.error = None
            self._persist(job)
            logger.info("Download job %s completed (%s files)", job.id, job.downloaded_count)
            return job
        except CatalogBlockedError as exc:
            job.status = DownloadJobStatus.WAITING
            job.error = f"Blocked by catalog API for {exc.retry_after_seconds:.0f}s"
            self._persist(job)
            raise
        except Exception as exc:
            job.status = DownloadJobStatus.FAILED
            job.finished_at = datetime.now(UTC)
            job.error = str(exc)
            self._persist(job)
            raise

    def _process_batch(self, job: DownloadJob, batch: list[str]) -> None:
        # Keep API names for mark_downloaded; use sanitized names for local storage.
        pairs = [(name, sanitize_filename(name)) for name in batch]
        missing = [
            (original, safe)
            for original, safe in pairs
            if self._files.get_by_filename(safe) is None
        ]

        if missing:
            zip_bytes = self._catalog.download([original for original, _ in missing])
            extracted = extract_zip_files(zip_bytes)
            for original, filename in missing:
                content = extracted.get(filename)
                if content is None:
                    raise FileNotFoundError(
                        f"ZIP archive missing member for {original!r} ({filename!r})"
                    )
                path = self._storage.write_bytes(filename, content)
                self._files.add(
                    DownloadedFile(
                        job_id=job.id,
                        filename=filename,
                        content_path=self._storage.relative_path(filename),
                        content_hash=hashlib.sha256(content).hexdigest(),
                        size_bytes=len(content),
                        downloaded_at=datetime.now(UTC),
                    )
                )
                job.downloaded_count += 1
                logger.debug("Saved %s (%s bytes) to %s", filename, len(content), path)
            self._persist(job)

        # Acknowledge only after successful local persistence/commit of new files.
        self._catalog.mark_downloaded(batch)

    def _persist(self, job: DownloadJob) -> None:
        self._jobs.update(job)
        self._commit()
        self._progress_store.save(
            JobProgressView(
                job_id=str(job.id),
                status=job.status.value,
                names_received=job.names_received,
                downloaded_count=job.downloaded_count,
                started_at=job.started_at.isoformat(),
                error=job.error,
            )
        )
