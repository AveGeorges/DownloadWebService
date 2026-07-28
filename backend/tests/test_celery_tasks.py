from datetime import UTC, datetime
from uuid import UUID, uuid4

import fakeredis
import pytest
from celery.exceptions import Retry
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities import DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import CatalogBlockedError, DownloadJobNotFoundError
from app.infrastructure.db.repositories import SqlAlchemyDownloadJobRepository
from app.workers import tasks as tasks_module


class _FakeCatalog:
    def close(self) -> None:
        return None


def test_celery_ping() -> None:
    assert tasks_module.ping() == "pong"


def test_run_download_job_success(
    monkeypatch: pytest.MonkeyPatch,
    session: Session,
    engine,
    tmp_path,
) -> None:
    job = SqlAlchemyDownloadJobRepository(session).add(
        DownloadJob(status=DownloadJobStatus.PENDING)
    )
    session.commit()

    fake_redis = fakeredis.FakeRedis()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    class _Settings:
        files_storage_path = str(tmp_path / "files")

    class _UseCase:
        def __init__(self, **_kwargs) -> None:
            return None

        def execute(self, job_id: UUID) -> DownloadJob:
            assert job_id == job.id
            return DownloadJob(
                id=job.id,
                status=DownloadJobStatus.COMPLETED,
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                names_received=3,
                downloaded_count=3,
            )

    monkeypatch.setattr(tasks_module, "get_settings", lambda: _Settings())
    monkeypatch.setattr(tasks_module, "build_redis_client", lambda _s: fake_redis)
    monkeypatch.setattr(tasks_module, "build_external_catalog_client", lambda _s: _FakeCatalog())
    monkeypatch.setattr(tasks_module, "get_session_factory", lambda: factory)
    monkeypatch.setattr(tasks_module, "RunDownloadJobUseCase", _UseCase)

    result = tasks_module.run_download_job.run(str(job.id))
    assert result["status"] == "completed"
    assert result["downloaded_count"] == 3
    assert fake_redis.get("download:active_job") is None


def test_run_download_job_retries_on_block(
    monkeypatch: pytest.MonkeyPatch,
    session: Session,
    engine,
    tmp_path,
) -> None:
    job = SqlAlchemyDownloadJobRepository(session).add(
        DownloadJob(status=DownloadJobStatus.PENDING)
    )
    session.commit()

    fake_redis = fakeredis.FakeRedis()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    class _Settings:
        files_storage_path = str(tmp_path / "files")

    class _UseCase:
        def __init__(self, **_kwargs) -> None:
            return None

        def execute(self, _job_id: UUID) -> DownloadJob:
            raise CatalogBlockedError("blocked", retry_after_seconds=12)

    monkeypatch.setattr(tasks_module, "get_settings", lambda: _Settings())
    monkeypatch.setattr(tasks_module, "build_redis_client", lambda _s: fake_redis)
    monkeypatch.setattr(tasks_module, "build_external_catalog_client", lambda _s: _FakeCatalog())
    monkeypatch.setattr(tasks_module, "get_session_factory", lambda: factory)
    monkeypatch.setattr(tasks_module, "RunDownloadJobUseCase", _UseCase)

    seen: dict[str, object] = {}

    def capture_retry(self, countdown=None, exc=None, **kwargs):
        seen["countdown"] = countdown
        seen["exc"] = exc
        raise Retry("retried", exc=exc, when=countdown)

    monkeypatch.setattr(tasks_module.run_download_job.__class__, "retry", capture_retry)

    with pytest.raises(Retry) as exc_info:
        tasks_module.run_download_job.run(str(job.id))
    assert seen["countdown"] == 12
    assert isinstance(seen["exc"], CatalogBlockedError)
    assert exc_info.value.when == 12


def test_run_download_job_releases_lock_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    engine,
    tmp_path,
) -> None:
    fake_redis = fakeredis.FakeRedis()
    missing_id = uuid4()
    fake_redis.set("download:active_job", str(missing_id))
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    class _Settings:
        files_storage_path = str(tmp_path / "files")

    class _UseCase:
        def __init__(self, **_kwargs) -> None:
            return None

        def execute(self, job_id: UUID) -> DownloadJob:
            raise DownloadJobNotFoundError(str(job_id))

    monkeypatch.setattr(tasks_module, "get_settings", lambda: _Settings())
    monkeypatch.setattr(tasks_module, "build_redis_client", lambda _s: fake_redis)
    monkeypatch.setattr(tasks_module, "build_external_catalog_client", lambda _s: _FakeCatalog())
    monkeypatch.setattr(tasks_module, "get_session_factory", lambda: factory)
    monkeypatch.setattr(tasks_module, "RunDownloadJobUseCase", _UseCase)

    with pytest.raises(DownloadJobNotFoundError):
        tasks_module.run_download_job.run(str(missing_id))

    assert fake_redis.get("download:active_job") is None


def test_run_download_job_releases_lock_on_generic_error(
    monkeypatch: pytest.MonkeyPatch,
    session: Session,
    engine,
    tmp_path,
) -> None:
    job = SqlAlchemyDownloadJobRepository(session).add(
        DownloadJob(status=DownloadJobStatus.PENDING)
    )
    session.commit()
    fake_redis = fakeredis.FakeRedis()
    fake_redis.set("download:active_job", str(job.id))
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    class _Settings:
        files_storage_path = str(tmp_path / "files")

    class _UseCase:
        def __init__(self, **_kwargs) -> None:
            return None

        def execute(self, _job_id: UUID) -> DownloadJob:
            raise RuntimeError("boom")

    monkeypatch.setattr(tasks_module, "get_settings", lambda: _Settings())
    monkeypatch.setattr(tasks_module, "build_redis_client", lambda _s: fake_redis)
    monkeypatch.setattr(tasks_module, "build_external_catalog_client", lambda _s: _FakeCatalog())
    monkeypatch.setattr(tasks_module, "get_session_factory", lambda: factory)
    monkeypatch.setattr(tasks_module, "RunDownloadJobUseCase", _UseCase)

    with pytest.raises(RuntimeError, match="boom"):
        tasks_module.run_download_job.run(str(job.id))

    assert fake_redis.get("download:active_job") is None
