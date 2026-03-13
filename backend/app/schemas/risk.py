from uuid import UUID

from pydantic import BaseModel


class EventImpactOut(BaseModel):
    event_id: UUID
    event_title: str
    event_category: str
    current_probability: float
    revenue_impact_per_day: float
    opex_impact_per_day: float
    capex_impact_per_day: float
    total_impact_per_day: float


class HedgeInstrumentOut(BaseModel):
    ticker: str
    instrument_type: str
    direction: str
    rationale: str


class MatchedEventOut(BaseModel):
    event_id: UUID
    event_title: str
    event_category: str
    current_probability: float
    relevance_score: int
    matched_themes: list[str]
    explanation: str


class CompanyRiskScoreResponse(BaseModel):
    company_id: UUID
    risk_score: int
    avg_score: float
    peak_score: int
    event_count: int
    matched_events: list[MatchedEventOut]


class MatchedCompanyOut(BaseModel):
    company_id: UUID
    name: str
    ticker: str | None = None
    sector: str
    relevance_score: int
    matched_themes: list[str]
    explanation: str


class PortfolioRiskSummary(BaseModel):
    total_companies: int
    avg_risk_score: float
    highest_risk: MatchedCompanyOut | None = None
    top_exposures: list[MatchedEventOut]
