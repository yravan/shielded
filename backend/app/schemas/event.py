from __future__ import annotations

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
    previous_probability: float | None = None
    resolution_date: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    parent_event_id: UUID | None = None
    parent_title: str | None = None
    is_parent: bool = False
    market_ticker: str | None = None
    children: list[EventOut] | None = None
    is_tracked: bool | None = None
    expected_value: float | None = None
    is_quantitative: bool = False
    image_url: str | None = None
    tags: list[str] | None = None
    volume: float | None = None

    model_config = ConfigDict(from_attributes=True)


EventOut.model_rebuild()

EventListResponse = PaginatedResponse[EventOut]


class SuggestedEventOut(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    region: str
    source: str
    source_url: str
    current_probability: float
    resolution_date: datetime | None = None
    status: str
    relevance_score: int
    matched_company_name: str
    matched_company_id: UUID
    matched_themes: list[str]
    parent_event_id: UUID | None = None
    parent_title: str | None = None
    image_url: str | None = None
    tags: list[str] | None = None


class ChildHistoryOut(BaseModel):
    title: str
    history: list[ProbabilityHistoryPoint] = []


class ChildrenHistoryResponse(BaseModel):
    children: dict[str, ChildHistoryOut] = {}
