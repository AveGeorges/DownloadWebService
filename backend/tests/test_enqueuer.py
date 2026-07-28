from uuid import uuid4

from app.infrastructure.celery.enqueuer import CeleryDownloadJobEnqueuer


def test_celery_enqueuer_calls_delay(monkeypatch) -> None:
    called: list[str] = []

    class _Task:
        @staticmethod
        def delay(job_id: str) -> None:
            called.append(job_id)

    monkeypatch.setattr(
        "app.infrastructure.celery.enqueuer.run_download_job_task",
        _Task(),
    )
    job_id = uuid4()
    CeleryDownloadJobEnqueuer().enqueue_run_download_job(job_id)
    assert called == [str(job_id)]
