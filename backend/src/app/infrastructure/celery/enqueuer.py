from uuid import UUID

from app.workers.tasks import run_download_job as run_download_job_task


class CeleryDownloadJobEnqueuer:
    def enqueue_run_download_job(self, job_id: UUID) -> None:
        run_download_job_task.delay(str(job_id))
