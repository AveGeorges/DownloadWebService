from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums import DownloadJobStatus


@dataclass(slots=True)
class DownloadJob:
    status: DownloadJobStatus = DownloadJobStatus.PENDING
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    error: str | None = None
    names_received: int = 0
    downloaded_count: int = 0
    total_known: int | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class DownloadedFile:
    filename: str
    content_path: str
    size_bytes: int
    job_id: UUID | None = None
    content_hash: str | None = None
    downloaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class DigitStatsCache:
    file_id: UUID
    counts: dict[str, int]
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
