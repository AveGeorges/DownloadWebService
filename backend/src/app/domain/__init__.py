"""Domain layer: entities, value objects, repository interfaces."""

from app.domain.entities import DigitStatsCache, DownloadedFile, DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import (
    CatalogBlockedError,
    CatalogRateLimitedError,
    CatalogRequestError,
    CatalogTransientError,
    DomainError,
    ExternalCatalogError,
    InvalidFilenameError,
)
from app.domain.filename import sanitize_filename

__all__ = [
    "CatalogBlockedError",
    "CatalogRateLimitedError",
    "CatalogRequestError",
    "CatalogTransientError",
    "DigitStatsCache",
    "DomainError",
    "DownloadJob",
    "DownloadJobStatus",
    "DownloadedFile",
    "ExternalCatalogError",
    "InvalidFilenameError",
    "sanitize_filename",
]
