from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import DigitStatsCache, DownloadedFile, DownloadJob
from app.domain.enums import DownloadJobStatus
from app.infrastructure.db.mappers import (
    file_to_entity,
    file_to_model,
    job_to_entity,
    job_to_model,
    stats_to_entity,
    stats_to_model,
)
from app.infrastructure.db.models import DigitStatsCacheModel, DownloadedFileModel, DownloadJobModel


class SqlAlchemyDownloadJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: DownloadJob) -> DownloadJob:
        model = job_to_model(job)
        self._session.add(model)
        self._session.flush()
        return job_to_entity(model)

    def get(self, job_id: UUID) -> DownloadJob | None:
        model = self._session.get(DownloadJobModel, job_id)
        return job_to_entity(model) if model else None

    def update(self, job: DownloadJob) -> DownloadJob:
        model = self._session.get(DownloadJobModel, job.id)
        if model is None:
            raise ValueError(f"DownloadJob not found: {job.id}")
        model.status = job.status
        model.started_at = job.started_at
        model.finished_at = job.finished_at
        model.error = job.error
        model.names_received = job.names_received
        model.downloaded_count = job.downloaded_count
        model.total_known = job.total_known
        self._session.flush()
        return job_to_entity(model)

    def list_by_status(self, status: DownloadJobStatus) -> Sequence[DownloadJob]:
        stmt = select(DownloadJobModel).where(DownloadJobModel.status == status)
        models = self._session.scalars(stmt).all()
        return [job_to_entity(model) for model in models]


class SqlAlchemyDownloadedFileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, file: DownloadedFile) -> DownloadedFile:
        model = file_to_model(file)
        self._session.add(model)
        self._session.flush()
        return file_to_entity(model)

    def get(self, file_id: UUID) -> DownloadedFile | None:
        model = self._session.get(DownloadedFileModel, file_id)
        return file_to_entity(model) if model else None

    def get_by_filename(self, filename: str) -> DownloadedFile | None:
        stmt = select(DownloadedFileModel).where(DownloadedFileModel.filename == filename)
        model = self._session.scalars(stmt).first()
        return file_to_entity(model) if model else None

    def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[DownloadedFile], int]:
        total = self._session.scalar(select(func.count()).select_from(DownloadedFileModel)) or 0
        stmt = (
            select(DownloadedFileModel)
            .order_by(DownloadedFileModel.downloaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.scalars(stmt).all()
        return [file_to_entity(model) for model in models], total

    def list_ids(self) -> Sequence[UUID]:
        stmt = select(DownloadedFileModel.id).order_by(DownloadedFileModel.downloaded_at.desc())
        return list(self._session.scalars(stmt).all())

    def list_by_ids(self, file_ids: Sequence[UUID]) -> Sequence[DownloadedFile]:
        if not file_ids:
            return []
        stmt = select(DownloadedFileModel).where(DownloadedFileModel.id.in_(file_ids))
        models = self._session.scalars(stmt).all()
        by_id = {model.id: file_to_entity(model) for model in models}
        return [by_id[file_id] for file_id in file_ids if file_id in by_id]


class SqlAlchemyDigitStatsCacheRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, cache: DigitStatsCache) -> DigitStatsCache:
        model = self._session.get(DigitStatsCacheModel, cache.file_id)
        if model is None:
            model = stats_to_model(cache)
            self._session.add(model)
        else:
            model.counts = dict(cache.counts)
            model.updated_at = cache.updated_at
        self._session.flush()
        return stats_to_entity(model)

    def get(self, file_id: UUID) -> DigitStatsCache | None:
        model = self._session.get(DigitStatsCacheModel, file_id)
        return stats_to_entity(model) if model else None

    def list_by_file_ids(self, file_ids: Sequence[UUID]) -> Sequence[DigitStatsCache]:
        if not file_ids:
            return []
        stmt = select(DigitStatsCacheModel).where(DigitStatsCacheModel.file_id.in_(file_ids))
        models = self._session.scalars(stmt).all()
        return [stats_to_entity(model) for model in models]
