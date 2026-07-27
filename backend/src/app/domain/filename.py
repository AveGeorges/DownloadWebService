import re
from pathlib import PurePosixPath

from app.domain.exceptions import InvalidFilenameError

_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


def sanitize_filename(filename: str) -> str:
    """Return a safe basename or raise InvalidFilenameError."""
    if not filename or not filename.strip():
        raise InvalidFilenameError("Filename is empty")

    name = PurePosixPath(filename.replace("\\", "/")).name
    if not name or name in {".", ".."}:
        raise InvalidFilenameError(f"Unsafe filename: {filename!r}")
    if not _SAFE_FILENAME.fullmatch(name):
        raise InvalidFilenameError(f"Invalid filename characters: {filename!r}")
    return name
