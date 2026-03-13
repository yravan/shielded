from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: UUID
    clerk_id: str
    email: str
    name: str | None = None
    created_at: datetime
    company_count: int = 0
    tracked_event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CompanyInput(BaseModel):
    name: str
    ticker: str | None = None
    sector: str
    annual_revenue: float = 0
    operating_expense: float = 0
    capital_expense: float = 0


class CompanyLookupResponse(BaseModel):
    name: str
    ticker: str
    sector: str | None = None
    annual_revenue: float | None = None
    operating_expense: float | None = None
    capital_expense: float | None = None
