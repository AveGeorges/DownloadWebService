from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.application.dto.job_progress import JobProgressView
from app.application.use_cases.get_download_job import GetDownloadJobUseCase
from app.domain.entities import DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import DownloadJobNotFoundError
from app.infrastructure.db.repositories import SqlAlchemyDownloadJobRepository
from tests.fakes import InMemoryProgressStore


def test_get_download_job_returns_progress(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    progress = InMemoryProgressStore()
    job = jobs.add(DownloadJob(status=DownloadJobStatus.RUNNING, names_received=3))
    session.commit()
    progress.save(
        JobProgressView(
            job_id=str(job.id),
            status="running",
            names_received=6,
            downloaded_count=2,
            started_at=job.started_at.isoformat(),
            error=None,
        )
    )

    loaded, view = GetDownloadJobUseCase(jobs=jobs, progress_store=progress).execute(job.id)
    assert loaded.id == job.id
    assert view is not None
    assert view.downloaded_count == 2


def test_get_download_job_not_found(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    progress = InMemoryProgressStore()
    with pytest.raises(DownloadJobNotFoundError):
        GetDownloadJobUseCase(jobs=jobs, progress_store=progress).execute(uuid4())
