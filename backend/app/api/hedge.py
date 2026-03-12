from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.models.hedge_analysis import HedgeAnalysis
from app.schemas.hedge import (
    HedgeComparisonResponse,
    PredictionMarketHedge,
    TraditionalHedge,
)
from app.services.hedge_calculator import (
    calculate_pm_hedge,
    calculate_traditional_hedge,
    recommend_hedge,
)

router = APIRouter(prefix="/api/hedge-analysis", tags=["hedge"])


@router.get("", response_model=HedgeComparisonResponse)
async def get_hedge_analysis(
    db: DbSession,
    company_id: UUID = Query(..., description="Company UUID"),
    event_id: UUID = Query(..., description="Event UUID"),
):
    # Check for pre-computed analysis
    result = await db.execute(
        select(HedgeAnalysis).where(
            HedgeAnalysis.company_id == company_id,
            HedgeAnalysis.event_id == event_id,
        )
    )
    analysis = result.scalar_one_or_none()

    # Load event
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Load company
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if analysis:
        return HedgeComparisonResponse(
            company_id=company_id,
            event_id=event_id,
            event_title=event.title,
            event_category=event.category,
            current_probability=event.current_probability,
            prediction_market=PredictionMarketHedge(
                cost=analysis.pm_cost,
                payout=analysis.pm_payout,
                roi=analysis.pm_roi,
            ),
            traditional=TraditionalHedge(
                instrument=analysis.traditional_instrument,
                cost=analysis.traditional_cost,
                payout=analysis.traditional_payout,
                roi=analysis.traditional_roi,
            ),
            recommendation=analysis.recommendation,
            savings_percent=analysis.savings_percent,
            notes=analysis.notes,
        )

    # Compute on the fly if no pre-computed analysis exists
    # Get exposure to determine notional
    exp_result = await db.execute(
        select(Exposure).where(
            Exposure.company_id == company_id,
            Exposure.event_id == event_id,
        )
    )
    exposure = exp_result.scalars().first()
    if not exposure:
        raise HTTPException(
            status_code=404,
            detail="No exposure found for this company-event pair",
        )

    notional = float(company.annual_revenue) * exposure.revenue_impact_pct * exposure.sensitivity
    probability = event.current_probability

    pm = calculate_pm_hedge(probability, notional)
    trad = calculate_traditional_hedge(event.category, notional, probability)
    rec = recommend_hedge(pm["roi"], trad["roi"], probability)

    savings = 0.0
    if trad["cost"] > 0:
        savings = round((trad["cost"] - pm["cost"]) / trad["cost"] * 100, 2)

    return HedgeComparisonResponse(
        company_id=company_id,
        event_id=event_id,
        event_title=event.title,
        event_category=event.category,
        current_probability=probability,
        prediction_market=PredictionMarketHedge(**pm),
        traditional=TraditionalHedge(**trad),
        recommendation=rec,
        savings_percent=savings,
    )
