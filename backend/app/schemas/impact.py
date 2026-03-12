from uuid import UUID

from pydantic import BaseModel


class ScenarioPoint(BaseModel):
    probability: float
    revenue_impact: float
    opex_impact: float
    capex_impact: float
    total_impact: float


class ImpactAnalysisResponse(BaseModel):
    company_id: UUID
    event_id: UUID
    scenarios: list[ScenarioPoint]
