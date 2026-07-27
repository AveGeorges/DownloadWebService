from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.application.use_cases.run_download_job import RunDownloadJobUseCase
from app.application.use_cases.start_download_job import StartDownloadJobUseCase
from app.domain.entities import DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import ActiveDownloadExistsError, CatalogBlockedError
from app.infrastructure.db.repositories import (
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)
from app.infrastructure.storage.file_storage import FileStorage
from tests.fakes import (
    FakeCatalog,
    InMemoryDownloadJobLock,
    InMemoryProgressStore,
    RecordingEnqueuer,
)


def _commit(session: Session) -> Callable[[], None]:
    return session.commit


def test_run_download_job_downloads_all_batches(
    session: Session,
    storage: FileStorage,
) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    progress = InMemoryProgressStore()

    job = jobs.add(DownloadJob(status=DownloadJobStatus.PENDING))
    session.commit()

    contents = {
        "a.txt": b"0" * 500,
        "b.txt": b"1" * 500,
        "c.txt": b"2" * 500,
        "d.txt": b"3" * 500,
    }
    catalog = FakeCatalog(
        batches=[["a.txt", "b.txt", "c.txt"], ["d.txt"]],
        contents=contents,
    )

    use_case = RunDownloadJobUseCase(
        jobs=jobs,
        files=files,
        catalog=catalog,
        storage=storage,
        progress_store=progress,
        commit=_commit(session),
    )
    result = use_case.execute(job.id)

    assert result.status == DownloadJobStatus.COMPLETED
    assert result.names_received == 4
    assert result.downloaded_count == 4
    assert set(catalog.marked) == {"a.txt", "b.txt", "c.txt", "d.txt"}
    assert catalog.download_calls == [["a.txt", "b.txt", "c.txt"], ["d.txt"]]
    assert storage.exists("a.txt")
    assert files.get_by_filename("d.txt") is not None
    assert progress.get(job.id) is not None
    assert progress.get(job.id).status == DownloadJobStatus.COMPLETED.value  # type: ignore[union-attr]


def test_run_download_job_is_idempotent_for_existing_files(
    session: Session,
    storage: FileStorage,
) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    progress = InMemoryProgressStore()

    job = jobs.add(DownloadJob(status=DownloadJobStatus.PENDING))
    session.commit()

    storage.write_bytes("a.txt", b"0" * 500)
    from app.domain.entities import DownloadedFile

    files.add(
        DownloadedFile(
            job_id=job.id,
            filename="a.txt",
            content_path="a.txt",
            size_bytes=500,
        )
    )
    session.commit()

    catalog = FakeCatalog(batches=[["a.txt", "b.txt"]], contents={"b.txt": b"1" * 500})
    use_case = RunDownloadJobUseCase(
        jobs=jobs,
        files=files,
        catalog=catalog,
        storage=storage,
        progress_store=progress,
        commit=_commit(session),
    )
    result = use_case.execute(job.id)

    assert result.status == DownloadJobStatus.COMPLETED
    assert result.downloaded_count == 1
    assert catalog.download_calls == [["b.txt"]]
    assert catalog.marked == ["a.txt", "b.txt"]


def test_run_download_job_sets_waiting_on_block(
    session: Session,
    storage: FileStorage,
) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    progress = InMemoryProgressStore()
    job = jobs.add(DownloadJob(status=DownloadJobStatus.PENDING))
    session.commit()

    class BlockingCatalog(FakeCatalog):
        def list_names(self) -> list[str]:
            raise CatalogBlockedError("blocked", retry_after_seconds=30)

    catalog = BlockingCatalog(batches=[], contents={})
    use_case = RunDownloadJobUseCase(
        jobs=jobs,
        files=files,
        catalog=catalog,
        storage=storage,
        progress_store=progress,
        commit=_commit(session),
    )

    with pytest.raises(CatalogBlockedError):
        use_case.execute(job.id)

    loaded = jobs.get(job.id)
    assert loaded is not None
    assert loaded.status == DownloadJobStatus.WAITING
    assert progress.get(job.id).status == DownloadJobStatus.WAITING.value  # type: ignore[union-attr]


def test_start_download_job_acquires_lock_and_enqueues(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    lock = InMemoryDownloadJobLock()
    progress = InMemoryProgressStore()
    enqueuer = RecordingEnqueuer()

    use_case = StartDownloadJobUseCase(
        jobs=jobs,
        lock=lock,
        progress_store=progress,
        enqueuer=enqueuer,
        commit=_commit(session),
    )
    job = use_case.execute()

    assert job.status == DownloadJobStatus.PENDING
    assert lock.holder == job.id
    assert enqueuer.jobs == [job.id]
    assert progress.get(job.id) is not None


def test_start_download_job_rejects_second_active(session: Session) -> None:
    jobs = SqlAlchemyDownloadJobRepository(session)
    lock = InMemoryDownloadJobLock()
    progress = InMemoryProgressStore()
    enqueuer = RecordingEnqueuer()

    first = StartDownloadJobUseCase(
        jobs=jobs,
        lock=lock,
        progress_store=progress,
        enqueuer=enqueuer,
        commit=_commit(session),
    ).execute()

    with pytest.raises(ActiveDownloadExistsError):
        StartDownloadJobUseCase(
            jobs=jobs,
            lock=lock,
            progress_store=progress,
            enqueuer=enqueuer,
            commit=_commit(session),
        ).execute()

    assert enqueuer.jobs == [first.id]
