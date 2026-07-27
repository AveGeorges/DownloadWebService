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
