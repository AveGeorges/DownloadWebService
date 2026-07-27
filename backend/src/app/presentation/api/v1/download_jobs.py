from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.application.use_cases.get_download_job import GetDownloadJobUseCase
from app.application.use_cases.start_download_job import StartDownloadJobUseCase
from app.domain.entities import DownloadJob
from app.domain.exceptions import ActiveDownloadExistsError, DownloadJobNotFoundError
from app.presentation.api.deps import (
    EnqueuerDep,
    JobLockDep,
    JobRepoDep,
    ProgressStoreDep,
    SessionDep,
)
from app.presentation.api.schemas import DownloadJobResponse, ErrorResponse

router = APIRouter(prefix="/download-jobs", tags=["download-jobs"])


def _to_response(job: DownloadJob) -> DownloadJobResponse:
    return DownloadJobResponse(
        id=job.id,
        status=job.status.value,
        started_at=job.started_at,
        finished_at=job.finished_at,
        names_received=job.names_received,
        downloaded_count=job.downloaded_count,
        total_known=job.total_known,
        error=job.error,
    )


@router.post(
    "",
    response_model=DownloadJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={409: {"model": ErrorResponse}},
)
def start_download_job(
    session: SessionDep,
    jobs: JobRepoDep,
    lock: JobLockDep,
    progress_store: ProgressStoreDep,
    enqueuer: EnqueuerDep,
) -> DownloadJobResponse:
    use_case = StartDownloadJobUseCase(
        jobs=jobs,
        lock=lock,
        progress_store=progress_store,
        enqueuer=enqueuer,
        commit=session.commit,
    )
    try:
        job = use_case.execute()
    except ActiveDownloadExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_response(job)


@router.get(
    "/{job_id}",
    response_model=DownloadJobResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_download_job(
    job_id: UUID,
    jobs: JobRepoDep,
    progress_store: ProgressStoreDep,
    response: Response,
) -> DownloadJobResponse:
    use_case = GetDownloadJobUseCase(jobs=jobs, progress_store=progress_store)
    try:
        job, progress = use_case.execute(job_id)
    except DownloadJobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    payload = _to_response(job)
    if progress is not None:
        payload = payload.model_copy(
            update={
                "status": progress.status or payload.status,
                "names_received": progress.names_received,
                "downloaded_count": progress.downloaded_count,
                "error": progress.error if progress.error is not None else payload.error,
            }
        )
    response.headers["Cache-Control"] = "no-store"
    return payload
