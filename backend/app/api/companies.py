import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, RedisConn
from app.models.company import Company
from app.models.exposure import Exposure
from app.schemas.company import CompanyExposureResponse, CompanyOut, ExposureOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
async def list_companies(db: DbSession):
    result = await db.execute(select(Company).order_by(Company.name))
    companies = result.scalars().all()
    return [CompanyOut.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: DbSession):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)


@router.get("/{company_id}/exposure", response_model=CompanyExposureResponse)
async def get_company_exposure(company_id: UUID, db: DbSession, redis_conn: RedisConn):
    cache_key = f"company:exposure:{company_id}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    exp_result = await db.execute(
        select(Exposure).where(Exposure.company_id == company_id)
    )
    exposures = exp_result.scalars().all()

    exposure_outs = []
    for exp in exposures:
        event = exp.event
        exposure_outs.append(
            ExposureOut(
                id=exp.id,
                company_id=exp.company_id,
                event_id=exp.event_id,
                exposure_type=exp.exposure_type,
                exposure_direction=exp.exposure_direction,
                sensitivity=exp.sensitivity,
                revenue_impact_pct=exp.revenue_impact_pct,
                opex_impact_pct=exp.opex_impact_pct,
                capex_impact_pct=exp.capex_impact_pct,
                notes=exp.notes,
                event_title=event.title if event else None,
                event_category=event.category if event else None,
                current_probability=event.current_probability if event else None,
            )
        )

    response = CompanyExposureResponse(
        company=CompanyOut.model_validate(company),
        exposures=exposure_outs,
    )

    await redis_conn.set(cache_key, response.model_dump_json(), ex=300)
    return response
