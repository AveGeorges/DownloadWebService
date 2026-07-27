from fastapi import APIRouter

from app.presentation.api.v1 import calculations, download_jobs, files

router = APIRouter()
router.include_router(download_jobs.router)
router.include_router(files.router)
router.include_router(calculations.router)


@router.get("/ping", tags=["v1"])
async def ping() -> dict[str, str]:
    return {"message": "pong"}
