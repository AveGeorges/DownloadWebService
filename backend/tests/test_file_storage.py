from pathlib import Path

from app.infrastructure.storage.file_storage import FileStorage


def test_file_storage_write_read(storage: FileStorage) -> None:
    path = storage.write_bytes("demo.txt", b"12345")
    assert path.is_file()
    assert storage.read_bytes("demo.txt") == b"12345"
    assert storage.exists("demo.txt")
    assert storage.relative_path("demo.txt") == "demo.txt"


def test_file_storage_normalizes_nested_path(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path / "files")
    path = storage.write_bytes("../escape.txt", b"x")
    assert path.parent == storage.root.resolve()
    assert path.name == "escape.txt"
    assert not (tmp_path / "escape.txt").exists()
