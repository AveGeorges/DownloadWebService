import pytest

from app.domain.exceptions import InvalidFilenameError
from app.domain.filename import sanitize_filename


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("file.txt", "file.txt"),
        ("dir/file_1.dat", "file_1.dat"),
        (r"dir\file-2.dat", "file-2.dat"),
        ("../secret.txt", "secret.txt"),
        ("file/../x.txt", "x.txt"),
    ],
)
def test_sanitize_filename_ok(raw: str, expected: str) -> None:
    assert sanitize_filename(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        " ",
        "..",
        ".",
        "file name.txt",
        "файл.txt",
        "a/b/c*",
    ],
)
def test_sanitize_filename_rejects_unsafe(raw: str) -> None:
    with pytest.raises(InvalidFilenameError):
        sanitize_filename(raw)
