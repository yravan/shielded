import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.database import async_session
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.models.hedge_analysis import HedgeAnalysis
from app.services.hedge_calculator import (
    calculate_pm_hedge,
    calculate_traditional_hedge,
    recommend_hedge,
)

logger = structlog.get_logger()


async def _recompute_hedges_async() -> dict:
    """Recompute hedge analyses for all company-event exposure pairs."""
    total_computed = 0

    async with async_session() as session:
        # Get all exposures with their company and event
        result = await session.execute(
            select(Exposure)
        )
        exposures = result.scalars().all()

        for exposure in exposures:
            try:
                # Load company and event
                company_result = await session.execute(
                    select(Company).where(Company.id == exposure.company_id)
                )
                company = company_result.scalar_one_or_none()

                event_result = await session.execute(
                    select(Event).where(Event.id == exposure.event_id)
                )
                event = event_result.scalar_one_or_none()

                if not company or not event:
                    continue

                if event.status != "active":
                    continue

                # Calculate notional exposure
                notional = (
                    float(company.annual_revenue)
                    * exposure.revenue_impact_pct
                    * exposure.sensitivity
                )

                if notional <= 0:
                    continue

                probability = event.current_probability

                # Calculate hedges
                pm = calculate_pm_hedge(probability, notional)
                trad = calculate_traditional_hedge(event.category, notional, probability)
                rec = recommend_hedge(pm["roi"], trad["roi"], probability)

                savings = 0.0
                if trad["cost"] > 0:
                    savings = round((trad["cost"] - pm["cost"]) / trad["cost"] * 100, 2)

                # Upsert hedge analysis
                existing_result = await session.execute(
                    select(HedgeAnalysis).where(
                        HedgeAnalysis.company_id == company.id,
                        HedgeAnalysis.event_id == event.id,
                    )
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    existing.pm_cost = pm["cost"]
                    existing.pm_payout = pm["payout"]
                    existing.pm_roi = pm["roi"]
                    existing.traditional_instrument = trad["instrument"]
                    existing.traditional_cost = trad["cost"]
                    existing.traditional_payout = trad["payout"]
                    existing.traditional_roi = trad["roi"]
                    existing.recommendation = rec
                    existing.savings_percent = savings
                    existing.computed_at = datetime.now(timezone.utc)
                else:
                    analysis = HedgeAnalysis(
                        id=uuid.uuid4(),
                        company_id=company.id,
                        event_id=event.id,
                        pm_cost=pm["cost"],
                        pm_payout=pm["payout"],
                        pm_roi=pm["roi"],
                        traditional_instrument=trad["instrument"],
                        traditional_cost=trad["cost"],
                        traditional_payout=trad["payout"],
                        traditional_roi=trad["roi"],
                        recommendation=rec,
                        savings_percent=savings,
                        computed_at=datetime.now(timezone.utc),
                    )
                    session.add(analysis)

                total_computed += 1

            except Exception as exc:
                await logger.awarning(
                    "Failed to compute hedge for exposure",
                    exposure_id=str(exposure.id),
                    error=str(exc),
                )

        await session.commit()

    await logger.ainfo("Hedge recomputation complete", total_computed=total_computed)
    return {"computed": total_computed}


try:
    from celery_app import celery

    @celery.task(name="app.tasks.hedges.recompute_hedges")
    def recompute_hedges() -> dict:
        """Celery task to recompute hedge analyses for all exposure pairs."""
        return asyncio.run(_recompute_hedges_async())

except ImportError:
    pass
