from pathlib import Path

from app.domain.filename import sanitize_filename


class FileStorage:
    """Stores downloaded file payloads on the local filesystem."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def resolve_path(self, filename: str) -> Path:
        safe_name = sanitize_filename(filename)
        path = (self._root / safe_name).resolve()
        if not str(path).startswith(str(self._root.resolve())):
            raise ValueError(f"Resolved path escapes storage root: {filename!r}")
        return path

    def write_bytes(self, filename: str, content: bytes) -> Path:
        path = self.resolve_path(filename)
        path.write_bytes(content)
        return path

    def read_bytes(self, filename: str) -> bytes:
        return self.resolve_path(filename).read_bytes()

    def exists(self, filename: str) -> bool:
        return self.resolve_path(filename).is_file()

    def relative_path(self, filename: str) -> str:
        return sanitize_filename(filename)
