from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.domain.entities import DownloadedFile
from app.domain.repositories import DownloadedFileRepository


class ListDownloadedFilesUseCase:
    def __init__(self, *, files: DownloadedFileRepository) -> None:
        self._files = files

    def execute(self, *, limit: int, offset: int) -> tuple[Sequence[DownloadedFile], int]:
        limit = min(max(limit, 1), 100)
        offset = max(offset, 0)
        return self._files.list_paginated(limit=limit, offset=offset)

    def list_all_ids(self) -> Sequence[UUID]:
        return self._files.list_ids()
