from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    id: UUID
    name: str
    ticker: str | None = None
    sector: str
    annual_revenue: float
    operating_expense: float
    capital_expense: float
    risk_profile: dict = {}
    risk_score: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExposureOut(BaseModel):
    id: UUID
    company_id: UUID
    event_id: UUID
    exposure_type: str
    exposure_direction: str
    sensitivity: float
    revenue_impact_pct: float
    opex_impact_pct: float
    capex_impact_pct: float
    status: str = "suggested"
    relevance_score: int | None = None
    matched_themes: list[str] | None = None
    notes: str | None = None
    event_title: str | None = None
    event_category: str | None = None
    current_probability: float | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyExposureResponse(BaseModel):
    company: CompanyOut
    exposures: list[ExposureOut]
