import pytest

from app.application.services.digit_stats import InvalidFileContentError, count_digits, merge_counts


def test_count_digits_ok() -> None:
    content = "0123456789" * 50
    counts = count_digits(content)
    assert counts["0"] == 50
    assert counts["9"] == 50
    assert sum(counts.values()) == 500


def test_count_digits_rejects_invalid() -> None:
    with pytest.raises(InvalidFileContentError):
        count_digits("123")
    with pytest.raises(InvalidFileContentError):
        count_digits("x" * 500)


def test_merge_counts() -> None:
    total = merge_counts({str(d): 0 for d in range(10)}, {"0": 2, "1": 3})
    total = merge_counts(total, {"0": 1})
    assert total["0"] == 3
    assert total["1"] == 3
