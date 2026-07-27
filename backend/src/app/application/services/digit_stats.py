from __future__ import annotations

from collections import Counter

EXPECTED_FILE_LENGTH = 500


class InvalidFileContentError(ValueError):
    """Raised when file content is not a 500-digit line."""


def count_digits(content: str) -> dict[str, int]:
    """Count digit occurrences in a catalog file payload."""
    normalized = content.strip()
    if len(normalized) != EXPECTED_FILE_LENGTH or not normalized.isdigit():
        raise InvalidFileContentError(
            f"Expected {EXPECTED_FILE_LENGTH} digits, got length={len(normalized)}"
        )
    counter = Counter(normalized)
    return {str(digit): int(counter.get(str(digit), 0)) for digit in range(10)}


def merge_counts(totals: dict[str, int], part: dict[str, int]) -> dict[str, int]:
    result = {str(digit): int(totals.get(str(digit), 0)) for digit in range(10)}
    for digit, value in part.items():
        result[str(digit)] = result.get(str(digit), 0) + int(value)
    return result
