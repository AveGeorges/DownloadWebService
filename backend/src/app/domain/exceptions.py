class DomainError(Exception):
    """Base domain error."""


class InvalidFilenameError(DomainError):
    """Raised when a filename is unsafe or empty."""


class ExternalCatalogError(DomainError):
    """Base error for external catalog interactions."""


class CatalogRateLimitedError(ExternalCatalogError):
    """Raised when the catalog API returns HTTP 429."""

    def __init__(self, message: str, *, retry_after_seconds: float) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CatalogBlockedError(ExternalCatalogError):
    """Raised when the catalog API blocks the client (HTTP 403)."""

    def __init__(self, message: str, *, retry_after_seconds: float) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CatalogRequestError(ExternalCatalogError):
    """Raised for non-retryable catalog HTTP/client errors."""


class CatalogTransientError(ExternalCatalogError):
    """Raised when retries are exhausted for transient failures."""


class ActiveDownloadExistsError(DomainError):
    """Raised when another download job already holds the global lock."""

    def __init__(self, message: str = "Another download job is already active") -> None:
        super().__init__(message)


class DownloadJobNotFoundError(DomainError):
    """Raised when a download job id does not exist."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"Download job not found: {job_id}")
        self.job_id = job_id
