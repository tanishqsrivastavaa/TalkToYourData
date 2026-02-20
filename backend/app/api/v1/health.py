"""Health-check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.db.engine import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    session: SQLModelAsyncSession = Depends(get_session),
) -> dict:
    """Return service status and verify database connectivity."""
    try:
        await session.exec(text("SELECT 1"))  # type: ignore[arg-type]
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {"status": "ok", "database": db_status}
