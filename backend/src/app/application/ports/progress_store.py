from typing import Protocol
from uuid import UUID

from app.application.dto.job_progress import JobProgressView


class JobProgressStore(Protocol):
    def save(self, progress: JobProgressView) -> None: ...

    def get(self, job_id: UUID) -> JobProgressView | None: ...
