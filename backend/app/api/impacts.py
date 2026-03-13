import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, RedisConn
from app.auth import get_current_user
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.schemas.impact import ImpactAnalysisResponse
from app.schemas.risk import EventImpactOut
from app.services.impact_calculator import calculate_scenarios

router = APIRouter(prefix="/api", tags=["impacts"])


@router.get("/impacts/{company_id}/{event_id}", response_model=ImpactAnalysisResponse)
async def get_impact_analysis(
    company_id: UUID,
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
):
    cache_key = f"impact:{company_id}:{event_id}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    # Load company
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Load event
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Load exposure
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

    scenarios = calculate_scenarios(
        annual_revenue=float(company.annual_revenue),
        operating_expense=float(company.operating_expense),
        capital_expense=float(company.capital_expense),
        revenue_impact_pct=exposure.revenue_impact_pct,
        opex_impact_pct=exposure.opex_impact_pct,
        capex_impact_pct=exposure.capex_impact_pct,
        sensitivity=exposure.sensitivity,
    )

    response = ImpactAnalysisResponse(
        company_id=company_id,
        event_id=event_id,
        scenarios=scenarios,
    )

    await redis_conn.set(cache_key, response.model_dump_json(), ex=300)
    return response


@router.get(
    "/companies/{company_id}/event-impacts",
    response_model=list[EventImpactOut],
)
async def get_company_event_impacts(
    company_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
):
    """Return daily financial impacts for ALL tracked events for a company.

    Uses exposure impact percentages × company financials × event probability
    to compute $/day figures.
    """
    cache_key = f"company-event-impacts:{company_id}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get all exposures for this company with events
    exp_result = await db.execute(
        select(Exposure, Event)
        .join(Event, Exposure.event_id == Event.id)
        .where(
            Exposure.company_id == company_id,
            Exposure.status.in_(["suggested", "confirmed"]),
            Event.status == "active",
        )
    )
    rows = exp_result.all()

    annual_revenue = float(company.annual_revenue or 0)
    operating_expense = float(company.operating_expense or 0)
    capital_expense = float(company.capital_expense or 0)

    impacts = []
    for exposure, event in rows:
        prob = event.current_probability
        sens = exposure.sensitivity

        rev_per_day = annual_revenue * exposure.revenue_impact_pct * prob * sens / 365
        opex_per_day = operating_expense * exposure.opex_impact_pct * prob * sens / 365
        capex_per_day = capital_expense * exposure.capex_impact_pct * prob * sens / 365
        total_per_day = rev_per_day + opex_per_day + capex_per_day

        impacts.append(EventImpactOut(
            event_id=event.id,
            event_title=event.title,
            event_category=event.category or "",
            current_probability=prob,
            revenue_impact_per_day=round(rev_per_day, 2),
            opex_impact_per_day=round(opex_per_day, 2),
            capex_impact_per_day=round(capex_per_day, 2),
            total_impact_per_day=round(total_per_day, 2),
        ))

    impacts.sort(key=lambda i: abs(i.total_impact_per_day), reverse=True)

    # Cache for 5 minutes
    await redis_conn.set(
        cache_key,
        json.dumps([i.model_dump(mode="json") for i in impacts]),
        ex=300,
    )
    return impacts
