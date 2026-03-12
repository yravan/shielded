from uuid import UUID

from pydantic import BaseModel


class PredictionMarketHedge(BaseModel):
    cost: float
    payout: float
    roi: float


class TraditionalHedge(BaseModel):
    instrument: str
    cost: float
    payout: float
    roi: float


class HedgeComparisonResponse(BaseModel):
    company_id: UUID
    event_id: UUID
    event_title: str
    event_category: str
    current_probability: float
    prediction_market: PredictionMarketHedge
    traditional: TraditionalHedge
    recommendation: str
    savings_percent: float
    notes: str | None = None
