from fastapi import APIRouter, Query

from app.application.use_cases.list_downloaded_files import ListDownloadedFilesUseCase
from app.presentation.api.deps import FileRepoDep
from app.presentation.api.schemas import (
    DownloadedFileResponse,
    FileIdsResponse,
    PaginatedFilesResponse,
)

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=PaginatedFilesResponse)
def list_files(
    files: FileRepoDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedFilesResponse:
    use_case = ListDownloadedFilesUseCase(files=files)
    items, total = use_case.execute(limit=limit, offset=offset)
    return PaginatedFilesResponse(
        items=[
            DownloadedFileResponse(
                id=item.id,
                filename=item.filename,
                downloaded_at=item.downloaded_at,
                size_bytes=item.size_bytes,
                job_id=item.job_id,
            )
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/select-all-ids", response_model=FileIdsResponse)
def select_all_ids(files: FileRepoDep) -> FileIdsResponse:
    use_case = ListDownloadedFilesUseCase(files=files)
    return FileIdsResponse(ids=list(use_case.list_all_ids()))
