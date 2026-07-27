from fastapi import APIRouter, HTTPException, status

from app.application.use_cases.calculate_digit_stats import CalculateDigitStatsUseCase
from app.presentation.api.deps import FileRepoDep, FileStorageDep, SessionDep, StatsRepoDep
from app.presentation.api.schemas import (
    CalculationRequest,
    CalculationResponse,
    FileDigitStatsResponse,
)

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("", response_model=CalculationResponse)
def calculate(
    body: CalculationRequest,
    session: SessionDep,
    files: FileRepoDep,
    stats: StatsRepoDep,
    storage: FileStorageDep,
) -> CalculationResponse:
    use_case = CalculateDigitStatsUseCase(
        files=files,
        stats_cache=stats,
        storage=storage,
    )
    try:
        result = use_case.execute(body.file_ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    session.commit()
    return CalculationResponse(
        total=result.total,
        per_file=[
            FileDigitStatsResponse(
                file_id=item.file_id,
                filename=item.filename,
                counts=item.counts,
            )
            for item in result.per_file
        ],
        errors=result.errors,
    )
