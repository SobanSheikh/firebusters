from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.database import engine

router = APIRouter()


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("")
async def health(response: Response) -> dict[str, str]:
    checks: dict[str, str] = {"api": "ok", "database": "ok"}

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "unavailable"

    if "unavailable" in checks.values():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        checks["status"] = "degraded"
    else:
        checks["status"] = "ok"
    return checks
