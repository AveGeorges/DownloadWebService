from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DownloadJobResponse(BaseModel):
    id: UUID
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    names_received: int
    downloaded_count: int
    total_known: int | None = None
    error: str | None = None


class DownloadedFileResponse(BaseModel):
    id: UUID
    filename: str
    downloaded_at: datetime
    size_bytes: int
    job_id: UUID | None = None


class PaginatedFilesResponse(BaseModel):
    items: list[DownloadedFileResponse]
    total: int
    limit: int
    offset: int


class FileIdsResponse(BaseModel):
    ids: list[UUID]


class CalculationRequest(BaseModel):
    file_ids: list[UUID] = Field(min_length=1, max_length=500)


class FileDigitStatsResponse(BaseModel):
    file_id: UUID
    filename: str
    counts: dict[str, int]


class CalculationResponse(BaseModel):
    total: dict[str, int]
    per_file: list[FileDigitStatsResponse]
    errors: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
