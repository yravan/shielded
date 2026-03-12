"""Seed the database with initial data.

Usage:
    python -m app.seed.run
"""

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

from app.database import async_session, engine
from app.logging import setup_logging
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.models.hedge_analysis import HedgeAnalysis
from app.models.probability_history import ProbabilityHistory
from app.seed.data import COMPANIES, EVENTS, EXPOSURES, HEDGE_ANALYSES
from app.seed.generator import generate_probability_history

setup_logging()
logger = structlog.get_logger()


async def seed_database() -> None:
    """Seed the database with initial data. Idempotent - skips if data exists."""
    async with async_session() as session:
        # Check if data already exists
        from sqlalchemy import func, select

        count_result = await session.execute(select(func.count(Event.id)))
        event_count = count_result.scalar_one()

        if event_count > 0:
            await logger.ainfo(
                "Database already seeded",
                event_count=event_count,
            )
            return

        await logger.ainfo("Seeding database...")

        # Insert events
        for event_data in EVENTS:
            event = Event(
                id=uuid.UUID(event_data["id"]),
                title=event_data["title"],
                description=event_data["description"],
                category=event_data["category"],
                region=event_data["region"],
                source=event_data["source"],
                source_id=event_data["source_id"],
                source_url=event_data["source_url"],
                current_probability=event_data["current_probability"],
                status=event_data["status"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(event)

        await session.flush()
        await logger.ainfo("Inserted events", count=len(EVENTS))

        # Insert companies
        for company_data in COMPANIES:
            company = Company(
                id=uuid.UUID(company_data["id"]),
                name=company_data["name"],
                ticker=company_data["ticker"],
                sector=company_data["sector"],
                annual_revenue=company_data["annual_revenue"],
                operating_expense=company_data["operating_expense"],
                capital_expense=company_data["capital_expense"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(company)

        await session.flush()
        await logger.ainfo("Inserted companies", count=len(COMPANIES))

        # Insert exposures
        for exp_data in EXPOSURES:
            exposure = Exposure(
                id=uuid.UUID(exp_data["id"]),
                company_id=uuid.UUID(exp_data["company_id"]),
                event_id=uuid.UUID(exp_data["event_id"]),
                exposure_type=exp_data["exposure_type"],
                exposure_direction=exp_data["exposure_direction"],
                sensitivity=exp_data["sensitivity"],
                revenue_impact_pct=exp_data["revenue_impact_pct"],
                opex_impact_pct=exp_data["opex_impact_pct"],
                capex_impact_pct=exp_data["capex_impact_pct"],
                notes=exp_data.get("notes"),
                created_at=datetime.now(timezone.utc),
            )
            session.add(exposure)

        await session.flush()
        await logger.ainfo("Inserted exposures", count=len(EXPOSURES))

        # Generate and insert probability histories
        total_history_points = 0
        for event_data in EVENTS:
            history = generate_probability_history(
                event_id=event_data["id"],
                base_prob=event_data["current_probability"],
                volatility=0.03,
                days=90,
                points_per_day=24,
            )
            for point in history:
                record = ProbabilityHistory(
                    event_id=uuid.UUID(point["event_id"]),
                    probability=point["probability"],
                    source_bid=point["source_bid"],
                    source_ask=point["source_ask"],
                    volume_24h=point["volume_24h"],
                    recorded_at=point["recorded_at"],
                )
                session.add(record)
            total_history_points += len(history)

        await session.flush()
        await logger.ainfo("Inserted probability history", count=total_history_points)

        # Insert hedge analyses
        for hedge_data in HEDGE_ANALYSES:
            analysis = HedgeAnalysis(
                id=uuid.UUID(hedge_data["id"]),
                company_id=uuid.UUID(hedge_data["company_id"]),
                event_id=uuid.UUID(hedge_data["event_id"]),
                pm_cost=hedge_data["pm_cost"],
                pm_payout=hedge_data["pm_payout"],
                pm_roi=hedge_data["pm_roi"],
                traditional_instrument=hedge_data["traditional_instrument"],
                traditional_cost=hedge_data["traditional_cost"],
                traditional_payout=hedge_data["traditional_payout"],
                traditional_roi=hedge_data["traditional_roi"],
                recommendation=hedge_data["recommendation"],
                savings_percent=hedge_data["savings_percent"],
                notes=hedge_data.get("notes"),
                computed_at=datetime.now(timezone.utc),
            )
            session.add(analysis)

        await session.commit()
        await logger.ainfo(
            "Database seeding complete",
            events=len(EVENTS),
            companies=len(COMPANIES),
            exposures=len(EXPOSURES),
            hedge_analyses=len(HEDGE_ANALYSES),
            history_points=total_history_points,
        )


async def main() -> None:
    try:
        await seed_database()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
