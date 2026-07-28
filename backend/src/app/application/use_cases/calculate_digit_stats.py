from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.services.chunking import chunked
from app.application.services.digit_stats import (
    InvalidFileContentError,
    count_digits,
    merge_counts,
)
from app.domain.entities import DigitStatsCache
from app.domain.repositories import DigitStatsCacheRepository, DownloadedFileRepository
from app.infrastructure.storage.file_storage import FileStorage

DEFAULT_MAX_CALCULATION_FILES = 10_000
DEFAULT_CALCULATION_BATCH_SIZE = 500


@dataclass(slots=True, frozen=True)
class FileDigitStats:
    file_id: UUID
    filename: str
    counts: dict[str, int]


@dataclass(slots=True, frozen=True)
class CalculationResult:
    total: dict[str, int]
    per_file: list[FileDigitStats]
    errors: list[str]


class CalculateDigitStatsUseCase:
    def __init__(
        self,
        *,
        files: DownloadedFileRepository,
        stats_cache: DigitStatsCacheRepository,
        storage: FileStorage,
        max_files: int = DEFAULT_MAX_CALCULATION_FILES,
        batch_size: int = DEFAULT_CALCULATION_BATCH_SIZE,
    ) -> None:
        self._files = files
        self._stats_cache = stats_cache
        self._storage = storage
        self._max_files = max_files
        self._batch_size = batch_size

    def execute(self, file_ids: list[UUID]) -> CalculationResult:
        unique_ids = list(dict.fromkeys(file_ids))
        if not unique_ids:
            raise ValueError("file_ids must not be empty")
        if len(unique_ids) > self._max_files:
            raise ValueError(f"Too many files selected (max {self._max_files})")

        errors: list[str] = []
        per_file: list[FileDigitStats] = []
        total = {str(digit): 0 for digit in range(10)}

        for batch in chunked(unique_ids, self._batch_size):
            entities = self._files.list_by_ids(batch)
            found = {item.id: item for item in entities}
            cached_by_id = {
                item.file_id: item for item in self._stats_cache.list_by_file_ids(batch)
            }

            for file_id in batch:
                entity = found.get(file_id)
                if entity is None:
                    errors.append(f"File not found: {file_id}")
                    continue

                cached = cached_by_id.get(file_id)
                if cached is not None:
                    counts = dict(cached.counts)
                else:
                    try:
                        raw = self._storage.read_bytes(entity.filename).decode("utf-8")
                        counts = count_digits(raw)
                    except (OSError, UnicodeDecodeError, InvalidFileContentError) as exc:
                        errors.append(f"{entity.filename}: {exc}")
                        continue
                    self._stats_cache.upsert(DigitStatsCache(file_id=file_id, counts=counts))

                per_file.append(
                    FileDigitStats(file_id=entity.id, filename=entity.filename, counts=counts)
                )
                total = merge_counts(total, counts)

        return CalculationResult(total=total, per_file=per_file, errors=errors)
