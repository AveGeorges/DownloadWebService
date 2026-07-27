import io
import zipfile

import pytest

from app.domain.exceptions import CatalogRequestError
from app.infrastructure.zip.extractor import extract_zip_files


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_extract_zip_files_sanitizes_nested_names() -> None:
    payload = _zip_bytes({"dir/a.txt": b"123", "b.txt": b"456"})
    result = extract_zip_files(payload)
    assert result == {"a.txt": b"123", "b.txt": b"456"}


def test_extract_zip_files_rejects_bad_payload() -> None:
    with pytest.raises(CatalogRequestError):
        extract_zip_files(b"not-a-zip")
