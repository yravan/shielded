import json
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, RedisConn
from app.api.users import get_or_create_user
from app.auth import get_current_user
from app.models.company import Company
from app.models.exposure import Exposure
from app.schemas.company import CompanyExposureResponse, CompanyOut, ExposureOut
from app.schemas.user import CompanyInput, CompanyLookupResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["companies"])


# ── Multi-company CRUD ──────────────────────────────────────────────────


@router.get("/my-companies", response_model=list[CompanyOut])
async def list_my_companies(db: DbSession, user: dict = Depends(get_current_user)):
    """List all companies for the current user."""
    db_user = await get_or_create_user(db, user)
    result = await db.execute(
        select(Company).where(Company.user_id == db_user.id).order_by(Company.created_at)
    )
    companies = result.scalars().all()
    return [CompanyOut.model_validate(c) for c in companies]


@router.post("/my-companies", response_model=CompanyOut)
async def create_my_company(
    body: CompanyInput,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Create a new company for the current user."""
    db_user = await get_or_create_user(db, user)

    company = Company(
        name=body.name,
        ticker=body.ticker,
        sector=body.sector,
        annual_revenue=body.annual_revenue,
        operating_expense=body.operating_expense,
        capital_expense=body.capital_expense,
        user_id=db_user.id,
    )
    db.add(company)
    await db.flush()

    return CompanyOut.model_validate(company)


@router.put("/my-companies/{company_id}", response_model=CompanyOut)
async def update_my_company(
    company_id: UUID,
    body: CompanyInput,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Update a specific company (verify ownership)."""
    db_user = await get_or_create_user(db, user)

    result = await db.execute(
        select(Company).where(Company.id == company_id, Company.user_id == db_user.id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.name = body.name
    company.ticker = body.ticker
    company.sector = body.sector
    company.annual_revenue = body.annual_revenue
    company.operating_expense = body.operating_expense
    company.capital_expense = body.capital_expense
    await db.flush()

    return CompanyOut.model_validate(company)


@router.delete("/my-companies/{company_id}")
async def delete_my_company(
    company_id: UUID,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Delete a specific company (verify ownership)."""
    db_user = await get_or_create_user(db, user)

    result = await db.execute(
        select(Company).where(Company.id == company_id, Company.user_id == db_user.id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await db.delete(company)
    await db.flush()
    return {"status": "ok"}


# ── Backward-compatible single-company endpoints ────────────────────────


@router.get("/my-company", response_model=CompanyOut)
async def get_my_company(db: DbSession, user: dict = Depends(get_current_user)):
    """Get the current user's first company (backward compat)."""
    db_user = await get_or_create_user(db, user)
    result = await db.execute(
        select(Company).where(Company.user_id == db_user.id).order_by(Company.created_at).limit(1)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="No company configured")
    return CompanyOut.model_validate(company)


@router.post("/my-company", response_model=CompanyOut)
async def save_my_company(
    body: CompanyInput,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Create or update the current user's first company (backward compat)."""
    db_user = await get_or_create_user(db, user)

    result = await db.execute(
        select(Company).where(Company.user_id == db_user.id).order_by(Company.created_at).limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.name = body.name
        existing.ticker = body.ticker
        existing.sector = body.sector
        existing.annual_revenue = body.annual_revenue
        existing.operating_expense = body.operating_expense
        existing.capital_expense = body.capital_expense
        await db.flush()
        return CompanyOut.model_validate(existing)

    company = Company(
        name=body.name,
        ticker=body.ticker,
        sector=body.sector,
        annual_revenue=body.annual_revenue,
        operating_expense=body.operating_expense,
        capital_expense=body.capital_expense,
        user_id=db_user.id,
    )
    db.add(company)
    await db.flush()

    return CompanyOut.model_validate(company)


# ── Ticker lookup ────────────────────────────────────────────────────────


@router.get("/company-lookup/{ticker}", response_model=CompanyLookupResponse)
async def company_lookup(ticker: str):
    """Look up company financials by ticker using yfinance."""
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or info.get("quoteType") is None:
            raise HTTPException(status_code=404, detail="Ticker not found")

        return CompanyLookupResponse(
            name=info.get("longName") or info.get("shortName", ticker.upper()),
            ticker=ticker.upper(),
            sector=info.get("sector"),
            annual_revenue=info.get("totalRevenue"),
            operating_expense=info.get("operatingExpenses") or info.get("totalOperatingExpenses"),
            capital_expense=info.get("capitalExpenditures"),
        )
    except ImportError:
        raise HTTPException(
            status_code=501, detail="yfinance not installed — ticker lookup unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        await logger.awarning("Ticker lookup failed", ticker=ticker, error=str(e))
        raise HTTPException(status_code=404, detail="Could not look up ticker")


# ── Generic company endpoints ────────────────────────────────────────────


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(db: DbSession):
    result = await db.execute(select(Company).order_by(Company.name))
    companies = result.scalars().all()
    return [CompanyOut.model_validate(c) for c in companies]


@router.get("/companies/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: DbSession):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)


@router.get("/companies/{company_id}/exposure", response_model=CompanyExposureResponse)
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
