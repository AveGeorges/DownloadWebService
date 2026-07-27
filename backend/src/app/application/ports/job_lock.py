from typing import Protocol
from uuid import UUID


class DownloadJobLock(Protocol):
    """Global lock ensuring only one download job runs at a time."""

    def acquire(self, job_id: UUID, *, ttl_seconds: int = 3600) -> bool:
        """Try to acquire lock for ``job_id``. Returns False if another job holds it."""

    def release(self, job_id: UUID) -> None:
        """Release lock if it belongs to ``job_id``."""

    def get_holder(self) -> UUID | None:
        """Return job id that currently holds the lock, if any."""
