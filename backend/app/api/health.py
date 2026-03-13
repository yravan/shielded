import structlog
from fastapi import APIRouter
from sqlalchemy import func, select, text

from app.database import async_session
from app.models.event import Event

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check including database, Redis, and ingestion status."""
    checks: dict = {"version": "0.1.0"}

    # Database check
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        from app.redis import get_redis

        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Ingestion status
    try:
        async with async_session() as session:
            result = await session.execute(
                select(func.count()).select_from(Event).where(Event.status == "active")
            )
            active_events = result.scalar() or 0
            checks["active_events"] = active_events

            # Use latest event update as ingestion freshness indicator
            result = await session.execute(
                select(func.max(Event.updated_at))
            )
            last_update = result.scalar()
            if last_update:
                checks["last_ingestion"] = last_update.isoformat()
            else:
                checks["last_ingestion"] = None
    except Exception as e:
        checks["ingestion"] = f"error: {e}"

    all_ok = (
        checks.get("database") == "ok"
        and checks.get("redis") == "ok"
    )
    checks["status"] = "ok" if all_ok else "degraded"

    return checks
