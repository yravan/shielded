import asyncio

from celery_app import celery


@celery.task(name="app.tasks.risk_scoring.run_risk_scoring")
def run_risk_scoring() -> dict:
    """Celery task to run risk matching and scoring for all companies."""
    from app.database import engine
    from app.services.risk_service import run_risk_matching

    # Dispose stale connections from previous asyncio.run() calls
    asyncio.run(engine.dispose())
    return asyncio.run(run_risk_matching())
