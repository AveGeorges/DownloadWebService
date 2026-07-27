"""Domain layer: entities, value objects, repository interfaces."""

from app.domain.entities import DigitStatsCache, DownloadedFile, DownloadJob
from app.domain.enums import DownloadJobStatus
from app.domain.exceptions import (
    ActiveDownloadExistsError,
    CatalogBlockedError,
    CatalogRateLimitedError,
    CatalogRequestError,
    CatalogTransientError,
    DomainError,
    DownloadJobNotFoundError,
    ExternalCatalogError,
    InvalidFilenameError,
)
from app.domain.filename import sanitize_filename

__all__ = [
    "ActiveDownloadExistsError",
    "CatalogBlockedError",
    "CatalogRateLimitedError",
    "CatalogRequestError",
    "CatalogTransientError",
    "DigitStatsCache",
    "DomainError",
    "DownloadJob",
    "DownloadJobNotFoundError",
    "DownloadJobStatus",
    "DownloadedFile",
    "ExternalCatalogError",
    "InvalidFilenameError",
    "sanitize_filename",
]
