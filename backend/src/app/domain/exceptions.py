class DomainError(Exception):
    """Base domain error."""


class InvalidFilenameError(DomainError):
    """Raised when a filename is unsafe or empty."""
