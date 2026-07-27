from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.entities import DownloadedFile, DownloadJob
from app.infrastructure.db.repositories import (
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.storage.file_storage import FileStorage
from app.main import create_app
from app.presentation.api.deps import (
    get_enqueuer,
    get_file_storage,
    get_job_lock,
    get_progress_store,
)
from tests.fakes import InMemoryDownloadJobLock, InMemoryProgressStore, RecordingEnqueuer


@pytest.fixture
def api_env(
    session: Session,
    storage: FileStorage,
) -> Generator[
    tuple[TestClient, InMemoryDownloadJobLock, RecordingEnqueuer, InMemoryProgressStore], None, None
]:
    app = create_app()
    lock = InMemoryDownloadJobLock()
    progress = InMemoryProgressStore()
    enqueuer = RecordingEnqueuer()

    def override_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_job_lock] = lambda: lock
    app.dependency_overrides[get_progress_store] = lambda: progress
    app.dependency_overrides[get_enqueuer] = lambda: enqueuer
    app.dependency_overrides[get_file_storage] = lambda: storage

    client = TestClient(app)
    yield client, lock, enqueuer, progress
    app.dependency_overrides.clear()


def test_start_and_get_download_job(api_env) -> None:
    client, lock, enqueuer, _progress = api_env
    response = client.post("/api/v1/download-jobs")
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "pending"
    job_id = payload["id"]
    assert lock.holder is not None
    assert str(lock.holder) == job_id
    assert len(enqueuer.jobs) == 1

    got = client.get(f"/api/v1/download-jobs/{job_id}")
    assert got.status_code == 200
    assert got.json()["id"] == job_id

    conflict = client.post("/api/v1/download-jobs")
    assert conflict.status_code == 409


def test_get_download_job_not_found(api_env) -> None:
    client, *_ = api_env
    response = client.get("/api/v1/download-jobs/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_list_files_and_select_all_ids(
    api_env,
    session: Session,
) -> None:
    client, *_ = api_env
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    job = jobs.add(DownloadJob())
    files.add(DownloadedFile(job_id=job.id, filename="a.txt", content_path="a.txt", size_bytes=500))
    files.add(DownloadedFile(job_id=job.id, filename="b.txt", content_path="b.txt", size_bytes=500))
    session.commit()

    listed = client.get("/api/v1/files?limit=10&offset=0")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    ids = client.post("/api/v1/files/select-all-ids")
    assert ids.status_code == 200
    assert len(ids.json()["ids"]) == 2


def test_calculations_endpoint(
    api_env,
    session: Session,
    storage: FileStorage,
) -> None:
    client, *_ = api_env
    jobs = SqlAlchemyDownloadJobRepository(session)
    files = SqlAlchemyDownloadedFileRepository(session)
    job = jobs.add(DownloadJob())
    storage.write_bytes("calc.txt", ("3" * 500).encode())
    file = files.add(
        DownloadedFile(
            job_id=job.id,
            filename="calc.txt",
            content_path="calc.txt",
            size_bytes=500,
        )
    )
    session.commit()

    response = client.post("/api/v1/calculations", json={"file_ids": [str(file.id)]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"]["3"] == 500
    assert payload["per_file"][0]["filename"] == "calc.txt"
    assert payload["errors"] == []
