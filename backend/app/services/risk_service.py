"""Glue layer between the pure risk engine and the database.

Converts DB models to engine dataclasses, calls engine functions,
and writes results back to the database.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.database import async_session
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.risk_engine import (
    CompanyInput,
    CompanyRiskResult,
    EventInput,
    ExposureMatch,
    compute_company_risk,
    estimate_impact_pcts,
    match_event_to_companies,
    score_event_for_company,
)

logger = structlog.get_logger()


def event_to_input(event: Event) -> EventInput:
    """Convert a DB Event to a risk engine EventInput."""
    return EventInput(
        title=event.title,
        description=event.description or "",
        category=event.category or "",
        tags=[],
        probability=event.current_probability,
    )


def company_to_input(company: Company) -> CompanyInput:
    """Convert a DB Company to a risk engine CompanyInput."""
    return CompanyInput(
        company_id=str(company.id),
        ticker=company.ticker or "",
        sector=company.sector or "",
        exposures=company.risk_profile or {},
    )


async def run_risk_matching() -> dict:
    """Update existing exposures and recompute company risk scores.

    Does NOT create new Exposure rows — those are created when a user
    tracks an event.  This batch job only refreshes scores/impact pcts
    on exposures that already exist and recomputes company risk scores.
    """
    total_updated = 0
    total_scored = 0

    async with async_session() as session:
        # Load active events
        result = await session.execute(
            select(Event).where(
                Event.status == "active",
                Event.is_parent == False,  # noqa: E712
            )
        )
        events = result.scalars().all()
        event_map = {e.id: e for e in events}

        # Load companies with risk profiles
        result = await session.execute(select(Company))
        companies = result.scalars().all()
        companies_with_profiles = [c for c in companies if c.risk_profile]

        if not companies_with_profiles or not events:
            await logger.ainfo(
                "Risk matching skipped",
                companies=len(companies_with_profiles),
                events=len(events),
            )
            return {"updated": 0, "scored": 0}

        company_map = {c.id: c for c in companies_with_profiles}

        # Track matches per company for risk score computation
        company_matches: dict[str, list[ExposureMatch]] = {
            str(c.id): [] for c in companies_with_profiles
        }

        # Load all existing exposures for active events
        result = await session.execute(
            select(Exposure).where(
                Exposure.event_id.in_([e.id for e in events]),
                Exposure.company_id.in_([c.id for c in companies_with_profiles]),
            )
        )
        existing_exposures = result.scalars().all()

        # Re-score each existing exposure
        for exposure in existing_exposures:
            event = event_map.get(exposure.event_id)
            company = company_map.get(exposure.company_id)
            if not event or not company:
                continue

            event_input = event_to_input(event)
            company_input = company_to_input(company)
            match = score_event_for_company(event_input, company_input)

            company_matches[str(company.id)].append(match)

            # Update the exposure with fresh scores
            exposure.relevance_score = match.relevance_score
            exposure.matched_themes = match.matched_themes
            exposure.sensitivity = match.relevance_score / 100.0
            impact_pcts = estimate_impact_pcts(
                match.matched_themes,
                match.relevance_score,
            )
            exposure.revenue_impact_pct = impact_pcts["revenue_impact_pct"]
            exposure.opex_impact_pct = impact_pcts["opex_impact_pct"]
            exposure.capex_impact_pct = impact_pcts["capex_impact_pct"]
            total_updated += 1

        # Compute and update risk scores for each company
        for company_id_str, matches in company_matches.items():
            company = company_map.get(uuid.UUID(company_id_str))
            if not company:
                continue
            risk_result = compute_company_risk(company_id_str, matches)
            company.risk_score = risk_result.risk_score
            total_scored += 1

        await session.commit()

    await logger.ainfo(
        "Risk matching complete",
        updated=total_updated,
        scored=total_scored,
    )
    return {"updated": total_updated, "scored": total_scored}


async def score_single_company(company_id: uuid.UUID) -> CompanyRiskResult | None:
    """Recompute risk score for a single company."""
    async with async_session() as session:
        result = await session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if not company or not company.risk_profile:
            return None

        company_input = company_to_input(company)

        result = await session.execute(
            select(Event).where(
                Event.status == "active",
                Event.is_parent == False,  # noqa: E712
            )
        )
        events = result.scalars().all()

        matches: list[ExposureMatch] = []
        for event in events:
            event_input = event_to_input(event)
            match = score_event_for_company(event_input, company_input)
            if match.relevance_score >= 20:
                matches.append(match)

        risk_result = compute_company_risk(str(company_id), matches)
        company.risk_score = risk_result.risk_score
        await session.commit()

        return risk_result


async def match_single_event(
    event_id: uuid.UUID,
) -> list[tuple[Company, ExposureMatch]]:
    """Find all companies affected by a specific event."""
    async with async_session() as session:
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            return []

        event_input = event_to_input(event)

        result = await session.execute(select(Company))
        companies = result.scalars().all()

        companies_with_profiles = [c for c in companies if c.risk_profile]
        company_inputs = [company_to_input(c) for c in companies_with_profiles]
        company_map = {str(c.id): c for c in companies_with_profiles}

        matches = match_event_to_companies(event_input, company_inputs, min_score=20)

        return [
            (company_map[cid], match)
            for cid, match in matches
            if cid in company_map
        ]


def theme_to_exposure_type(theme: str) -> str:
    """Map a risk theme to an exposure type category."""
    mapping = {
        "taiwan_china_conflict": "supply_chain",
        "export_controls": "regulatory",
        "recession": "revenue",
        "oil_shock": "operational",
        "semiconductor": "supply_chain",
        "shipping": "supply_chain",
        "tariff": "revenue",
        "inflation": "operational",
        "interest_rate": "revenue",
        "climate": "operational",
        "regulation": "regulatory",
        "cyber": "operational",
        "middle_east": "supply_chain",
        "russia_ukraine": "supply_chain",
    }
    return mapping.get(theme, "operational")
