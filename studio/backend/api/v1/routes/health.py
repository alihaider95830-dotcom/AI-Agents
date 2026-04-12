from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.api.deps import get_db

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@router.get("/health/db", response_model=None)
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"db": "error", "detail": str(exc)},
        )

    return {"db": "ok"}
