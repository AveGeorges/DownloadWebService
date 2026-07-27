from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.entities import DigitStatsCache, DownloadedFile, DownloadJob
from app.domain.enums import DownloadJobStatus
from app.infrastructure.db.repositories import (
    SqlAlchemyDigitStatsCacheRepository,
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)


def test_download_job_repository_roundtrip(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    job = DownloadJob(status=DownloadJobStatus.PENDING)
    saved = jobs.add(job)
    session.commit()

    loaded = jobs.get(saved.id)
    assert loaded is not None
    assert loaded.status == DownloadJobStatus.PENDING

    loaded.status = DownloadJobStatus.RUNNING
    loaded.names_received = 6
    loaded.downloaded_count = 3
    updated = jobs.update(loaded)
    session.commit()

    assert updated.status == DownloadJobStatus.RUNNING
    assert updated.names_received == 6
    assert jobs.list_by_status(DownloadJobStatus.RUNNING)[0].id == saved.id


def test_downloaded_file_repository_pagination_and_unique(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)

    job = jobs.add(DownloadJob())
    now = datetime.now(UTC)
    first = files.add(
        DownloadedFile(
            job_id=job.id,
            filename="a.txt",
            content_path="a.txt",
            size_bytes=500,
            downloaded_at=now - timedelta(minutes=1),
        )
    )
    second = files.add(
        DownloadedFile(
            job_id=job.id,
            filename="b.txt",
            content_path="b.txt",
            size_bytes=500,
            downloaded_at=now,
        )
    )
    session.commit()

    page, total = files.list_paginated(limit=10, offset=0)
    assert total == 2
    assert [item.filename for item in page] == ["b.txt", "a.txt"]
    assert files.get_by_filename("a.txt") is not None
    assert files.list_ids() == [second.id, first.id]
    assert [item.id for item in files.list_by_ids([first.id, second.id])] == [first.id, second.id]


def test_digit_stats_cache_upsert(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    stats = SqlAlchemyDigitStatsCacheRepository(session)

    job = jobs.add(DownloadJob())
    file = files.add(
        DownloadedFile(
            job_id=job.id,
            filename="stats.txt",
            content_path="stats.txt",
            size_bytes=500,
        )
    )
    session.commit()

    counts = {str(digit): digit for digit in range(10)}
    cached = stats.upsert(DigitStatsCache(file_id=file.id, counts=counts))
    session.commit()
    assert cached.counts["9"] == 9

    cached.counts["0"] = 42
    stats.upsert(cached)
    session.commit()

    loaded = stats.get(file.id)
    assert loaded is not None
    assert loaded.counts["0"] == 42
    assert stats.get(uuid4()) is None
