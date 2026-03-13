import uuid

import structlog
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.auth import require_auth
from app.database import async_session
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.schemas.risk import (
    CompanyRiskScoreResponse,
    MatchedCompanyOut,
    MatchedEventOut,
    PortfolioRiskSummary,
)
from app.services.risk_service import match_single_event, score_single_company

logger = structlog.get_logger()

router = APIRouter(tags=["risk"])


@router.get("/api/companies/{company_id}/risk-score", response_model=CompanyRiskScoreResponse)
async def get_company_risk_score(company_id: uuid.UUID):
    """Get risk score and matched events for a company."""
    async with async_session() as session:
        result = await session.execute(
            select(Company).where(Company.id == company_id)
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get exposures with their events for match details
        result = await session.execute(
            select(Exposure, Event)
            .join(Event, Exposure.event_id == Event.id)
            .where(
                Exposure.company_id == company_id,
                Exposure.relevance_score.is_not(None),
            )
            .order_by(Exposure.relevance_score.desc())
        )
        rows = result.all()

        matched_events = [
            MatchedEventOut(
                event_id=event.id,
                event_title=event.title,
                event_category=event.category,
                current_probability=event.current_probability,
                relevance_score=exposure.relevance_score or 0,
                matched_themes=exposure.matched_themes or [],
                explanation=exposure.notes or "",
            )
            for exposure, event in rows
        ]

        # Use cached risk score or recompute
        risk_result = await score_single_company(company_id)
        if risk_result:
            return CompanyRiskScoreResponse(
                company_id=company_id,
                risk_score=risk_result.risk_score,
                avg_score=risk_result.avg_score,
                peak_score=risk_result.peak_score,
                event_count=risk_result.event_count,
                matched_events=matched_events,
            )

        return CompanyRiskScoreResponse(
            company_id=company_id,
            risk_score=company.risk_score or 0,
            avg_score=0.0,
            peak_score=0,
            event_count=len(matched_events),
            matched_events=matched_events,
        )


@router.get("/api/events/{event_id}/matched-companies", response_model=list[MatchedCompanyOut])
async def get_matched_companies(event_id: uuid.UUID):
    """Get all companies affected by an event with relevance scores."""
    async with async_session() as session:
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Event not found")

    matches = await match_single_event(event_id)
    return [
        MatchedCompanyOut(
            company_id=company.id,
            name=company.name,
            ticker=company.ticker,
            sector=company.sector,
            relevance_score=match.relevance_score,
            matched_themes=match.matched_themes,
            explanation=match.explanation,
        )
        for company, match in matches
    ]


@router.get("/api/portfolio/risk-summary", response_model=PortfolioRiskSummary)
async def get_portfolio_risk_summary(user_id: str = require_auth):
    """Get aggregate risk summary across all user companies."""
    async with async_session() as session:
        result = await session.execute(
            select(Company).where(Company.user_id == uuid.UUID(user_id))
        )
        companies = result.scalars().all()

        if not companies:
            return PortfolioRiskSummary(
                total_companies=0,
                avg_risk_score=0.0,
                highest_risk=None,
                top_exposures=[],
            )

        scores = [c.risk_score for c in companies if c.risk_score is not None]
        avg = sum(scores) / len(scores) if scores else 0.0

        # Find highest risk company
        highest = max(companies, key=lambda c: c.risk_score or 0)
        highest_risk = None
        if highest.risk_score:
            highest_risk = MatchedCompanyOut(
                company_id=highest.id,
                name=highest.name,
                ticker=highest.ticker,
                sector=highest.sector,
                relevance_score=highest.risk_score,
                matched_themes=[],
                explanation="",
            )

        # Get top exposures across all user companies
        company_ids = [c.id for c in companies]
        result = await session.execute(
            select(Exposure, Event)
            .join(Event, Exposure.event_id == Event.id)
            .where(
                Exposure.company_id.in_(company_ids),
                Exposure.relevance_score.is_not(None),
            )
            .order_by(Exposure.relevance_score.desc())
            .limit(10)
        )
        rows = result.all()

        top_exposures = [
            MatchedEventOut(
                event_id=event.id,
                event_title=event.title,
                event_category=event.category,
                current_probability=event.current_probability,
                relevance_score=exposure.relevance_score or 0,
                matched_themes=exposure.matched_themes or [],
                explanation=exposure.notes or "",
            )
            for exposure, event in rows
        ]

        return PortfolioRiskSummary(
            total_companies=len(companies),
            avg_risk_score=round(avg, 1),
            highest_risk=highest_risk,
            top_exposures=top_exposures,
        )


@router.put("/api/exposures/{exposure_id}/accept")
async def accept_exposure(exposure_id: uuid.UUID, user_id: str = require_auth):
    """Accept a suggested exposure, making it active for hedge calculations."""
    async with async_session() as session:
        result = await session.execute(
            select(Exposure).where(Exposure.id == exposure_id)
        )
        exposure = result.scalar_one_or_none()
        if not exposure:
            raise HTTPException(status_code=404, detail="Exposure not found")
        exposure.status = "confirmed"
        await session.commit()
        return {"status": "confirmed"}


@router.put("/api/exposures/{exposure_id}/dismiss")
async def dismiss_exposure(exposure_id: uuid.UUID, user_id: str = require_auth):
    """Dismiss a suggested exposure."""
    async with async_session() as session:
        result = await session.execute(
            select(Exposure).where(Exposure.id == exposure_id)
        )
        exposure = result.scalar_one_or_none()
        if not exposure:
            raise HTTPException(status_code=404, detail="Exposure not found")
        exposure.status = "dismissed"
        await session.commit()
        return {"status": "dismissed"}
