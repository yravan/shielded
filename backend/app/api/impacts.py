import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, RedisConn
from app.models.company import Company
from app.models.event import Event
from app.models.exposure import Exposure
from app.schemas.impact import ImpactAnalysisResponse
from app.services.impact_calculator import calculate_scenarios

router = APIRouter(prefix="/api/impacts", tags=["impacts"])


@router.get("/{company_id}/{event_id}", response_model=ImpactAnalysisResponse)
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
