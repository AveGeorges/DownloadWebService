from __future__ import annotations

import io
import zipfile
from collections.abc import Sequence
from uuid import UUID

from app.application.dto.job_progress import JobProgressView


class InMemoryProgressStore:
    def __init__(self) -> None:
        self.items: dict[str, JobProgressView] = {}

    def save(self, progress: JobProgressView) -> None:
        self.items[progress.job_id] = progress

    def get(self, job_id: UUID) -> JobProgressView | None:
        return self.items.get(str(job_id))


class InMemoryDownloadJobLock:
    def __init__(self) -> None:
        self.holder: UUID | None = None

    def acquire(self, job_id: UUID, *, ttl_seconds: int = 3600) -> bool:
        _ = ttl_seconds
        if self.holder is not None:
            return False
        self.holder = job_id
        return True

    def release(self, job_id: UUID) -> None:
        if self.holder == job_id:
            self.holder = None

    def get_holder(self) -> UUID | None:
        return self.holder


class RecordingEnqueuer:
    def __init__(self) -> None:
        self.jobs: list[UUID] = []

    def enqueue_run_download_job(self, job_id: UUID) -> None:
        self.jobs.append(job_id)


class FakeCatalog:
    """In-memory catalog that yields name batches until exhausted."""

    def __init__(
        self,
        batches: list[list[str]],
        contents: dict[str, bytes],
    ) -> None:
        self._batches = [list(batch) for batch in batches]
        self._contents = contents
        self.marked: list[str] = []
        self.download_calls: list[list[str]] = []

    def list_names(self) -> list[str]:
        if not self._batches:
            return []
        return list(self._batches.pop(0))

    def download(self, names: Sequence[str]) -> bytes:
        batch = list(names)
        self.download_calls.append(batch)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w") as archive:
            for name in batch:
                archive.writestr(name, self._contents[name])
        return buffer.getvalue()

    def mark_downloaded(self, names: Sequence[str]) -> None:
        self.marked.extend(list(names))
