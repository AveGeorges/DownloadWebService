from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

import redis
from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.job_lock import DownloadJobLock
from app.application.ports.progress_store import JobProgressStore
from app.application.ports.task_enqueuer import DownloadJobEnqueuer
from app.config import Settings, get_settings
from app.infrastructure.celery.enqueuer import CeleryDownloadJobEnqueuer
from app.infrastructure.db.repositories import (
    SqlAlchemyDigitStatsCacheRepository,
    SqlAlchemyDownloadedFileRepository,
    SqlAlchemyDownloadJobRepository,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.redis.client import build_redis_client
from app.infrastructure.redis.job_lock import RedisDownloadJobLock
from app.infrastructure.redis.progress_store import RedisJobProgressStore
from app.infrastructure.storage.file_storage import FileStorage

SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_redis(settings: SettingsDep) -> Generator[redis.Redis, None, None]:
    client = build_redis_client(settings)
    try:
        yield client
    finally:
        client.close()


RedisDep = Annotated[redis.Redis, Depends(get_redis)]


def get_job_lock(redis_client: RedisDep) -> DownloadJobLock:
    return RedisDownloadJobLock(redis_client)


def get_progress_store(redis_client: RedisDep) -> JobProgressStore:
    return RedisJobProgressStore(redis_client)


def get_enqueuer() -> DownloadJobEnqueuer:
    return CeleryDownloadJobEnqueuer()


def get_file_storage(settings: SettingsDep) -> FileStorage:
    return FileStorage(settings.files_storage_path)


def get_job_repo(session: SessionDep) -> SqlAlchemyDownloadJobRepository:
    return SqlAlchemyDownloadJobRepository(session)


def get_file_repo(session: SessionDep) -> SqlAlchemyDownloadedFileRepository:
    return SqlAlchemyDownloadedFileRepository(session)


def get_stats_repo(session: SessionDep) -> SqlAlchemyDigitStatsCacheRepository:
    return SqlAlchemyDigitStatsCacheRepository(session)


JobLockDep = Annotated[DownloadJobLock, Depends(get_job_lock)]
ProgressStoreDep = Annotated[JobProgressStore, Depends(get_progress_store)]
EnqueuerDep = Annotated[DownloadJobEnqueuer, Depends(get_enqueuer)]
FileStorageDep = Annotated[FileStorage, Depends(get_file_storage)]
JobRepoDep = Annotated[SqlAlchemyDownloadJobRepository, Depends(get_job_repo)]
FileRepoDep = Annotated[SqlAlchemyDownloadedFileRepository, Depends(get_file_repo)]
StatsRepoDep = Annotated[SqlAlchemyDigitStatsCacheRepository, Depends(get_stats_repo)]
