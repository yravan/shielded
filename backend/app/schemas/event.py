from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginatedResponse


class ProbabilityHistoryPoint(BaseModel):
    date: datetime
    probability: float
    volume: float | None = None


class EventOut(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    region: str
    source: str
    source_id: str
    source_url: str
    current_probability: float
    resolution_date: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


EventListResponse = PaginatedResponse[EventOut]
