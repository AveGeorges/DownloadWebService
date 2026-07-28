from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.application.use_cases.calculate_digit_stats import CalculateDigitStatsUseCase
from app.domain.entities import DownloadedFile, DownloadJob
from app.infrastructure.db.repositories import (
    SqlAlchemyDigitStatsCacheRepository,
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)
from app.infrastructure.storage.file_storage import FileStorage


def test_calculate_digit_stats_aggregates(session: Session, storage: FileStorage) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    stats = SqlAlchemyDigitStatsCacheRepository(session)

    job = jobs.add(DownloadJob())
    content_a = "0" * 500
    content_b = "1" * 250 + "2" * 250
    storage.write_bytes("a.txt", content_a.encode())
    storage.write_bytes("b.txt", content_b.encode())
    file_a = files.add(
        DownloadedFile(job_id=job.id, filename="a.txt", content_path="a.txt", size_bytes=500)
    )
    file_b = files.add(
        DownloadedFile(job_id=job.id, filename="b.txt", content_path="b.txt", size_bytes=500)
    )
    session.commit()

    result = CalculateDigitStatsUseCase(
        files=files,
        stats_cache=stats,
        storage=storage,
    ).execute([file_a.id, file_b.id])
    session.commit()

    assert result.total["0"] == 500
    assert result.total["1"] == 250
    assert result.total["2"] == 250
    assert len(result.per_file) == 2
    assert result.errors == []
    assert stats.get(file_a.id) is not None


def test_calculate_digit_stats_reports_missing(session: Session, storage: FileStorage) -> None:
    files = SqlAlchemyDownloadedFileRepository(session)
    stats = SqlAlchemyDigitStatsCacheRepository(session)
    missing_id = uuid4()
    result = CalculateDigitStatsUseCase(
        files=files,
        stats_cache=stats,
        storage=storage,
    ).execute([missing_id])
    assert result.per_file == []
    assert any(str(missing_id) in err for err in result.errors)


def test_calculate_digit_stats_batches_and_merges(session: Session, storage: FileStorage) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    stats = SqlAlchemyDigitStatsCacheRepository(session)
    job = jobs.add(DownloadJob())

    ids = []
    for index in range(5):
        name = f"f{index}.txt"
        storage.write_bytes(name, b"9" * 500)
        entity = files.add(
            DownloadedFile(job_id=job.id, filename=name, content_path=name, size_bytes=500)
        )
        ids.append(entity.id)
    session.commit()

    result = CalculateDigitStatsUseCase(
        files=files,
        stats_cache=stats,
        storage=storage,
        batch_size=2,
    ).execute(ids)

    assert len(result.per_file) == 5
    assert result.total["9"] == 2500
    assert result.errors == []


def test_calculate_digit_stats_rejects_over_max(session: Session, storage: FileStorage) -> None:
    files = SqlAlchemyDownloadedFileRepository(session)
    stats = SqlAlchemyDigitStatsCacheRepository(session)
    too_many = [uuid4() for _ in range(3)]

    with pytest.raises(ValueError, match="Too many files"):
        CalculateDigitStatsUseCase(
            files=files,
            stats_cache=stats,
            storage=storage,
            max_files=2,
        ).execute(too_many)
