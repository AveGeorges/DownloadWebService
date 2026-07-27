from typing import Protocol
from uuid import UUID


class DownloadJobEnqueuer(Protocol):
    def enqueue_run_download_job(self, job_id: UUID) -> None: ...
