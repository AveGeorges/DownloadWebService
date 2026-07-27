from app.domain.entities import DigitStatsCache, DownloadedFile, DownloadJob
from app.infrastructure.db.models import DigitStatsCacheModel, DownloadedFileModel, DownloadJobModel


def job_to_entity(model: DownloadJobModel) -> DownloadJob:
    return DownloadJob(
        id=model.id,
        status=model.status,
        started_at=model.started_at,
        finished_at=model.finished_at,
        error=model.error,
        names_received=model.names_received,
        downloaded_count=model.downloaded_count,
        total_known=model.total_known,
    )


def job_to_model(entity: DownloadJob) -> DownloadJobModel:
    return DownloadJobModel(
        id=entity.id,
        status=entity.status,
        started_at=entity.started_at,
        finished_at=entity.finished_at,
        error=entity.error,
        names_received=entity.names_received,
        downloaded_count=entity.downloaded_count,
        total_known=entity.total_known,
    )


def file_to_entity(model: DownloadedFileModel) -> DownloadedFile:
    return DownloadedFile(
        id=model.id,
        job_id=model.job_id,
        filename=model.filename,
        content_path=model.content_path,
        content_hash=model.content_hash,
        downloaded_at=model.downloaded_at,
        size_bytes=model.size_bytes,
    )


def file_to_model(entity: DownloadedFile) -> DownloadedFileModel:
    return DownloadedFileModel(
        id=entity.id,
        job_id=entity.job_id,
        filename=entity.filename,
        content_path=entity.content_path,
        content_hash=entity.content_hash,
        downloaded_at=entity.downloaded_at,
        size_bytes=entity.size_bytes,
    )


def stats_to_entity(model: DigitStatsCacheModel) -> DigitStatsCache:
    return DigitStatsCache(
        file_id=model.file_id,
        counts=dict(model.counts),
        updated_at=model.updated_at,
    )


def stats_to_model(entity: DigitStatsCache) -> DigitStatsCacheModel:
    return DigitStatsCacheModel(
        file_id=entity.file_id,
        counts=dict(entity.counts),
        updated_at=entity.updated_at,
    )
