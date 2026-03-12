import json
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import DbSession, RedisConn
from app.models.event import Event
from app.models.probability_history import ProbabilityHistory
from app.schemas.event import EventListResponse, EventOut, ProbabilityHistoryPoint

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    db: DbSession,
    redis_conn: RedisConn,
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query("active", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    cache_key = f"events:list:{category}:{status}:{page}:{page_size}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(Event)
    count_query = select(func.count(Event.id))

    if category:
        query = query.where(Event.category == category)
        count_query = count_query.where(Event.category == category)
    if status:
        query = query.where(Event.status == status)
        count_query = count_query.where(Event.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Event.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    events = result.scalars().all()

    response = EventListResponse(
        items=[EventOut.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )

    await redis_conn.set(cache_key, response.model_dump_json(), ex=60)
    return response


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: UUID, db: DbSession):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventOut.model_validate(event)


@router.get("/{event_id}/history", response_model=list[ProbabilityHistoryPoint])
async def get_event_history(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    hours: int = Query(2160, ge=1, le=8760, description="Hours of history to return"),
    bucket_minutes: int = Query(
        60, ge=1, le=1440, description="Bucket size in minutes for aggregation"
    ),
):
    cache_key = f"events:history:{event_id}:{hours}:{bucket_minutes}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    # Verify event exists
    event_result = await db.execute(select(Event.id).where(Event.id == event_id))
    if not event_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(ProbabilityHistory)
        .where(ProbabilityHistory.event_id == event_id)
        .where(ProbabilityHistory.recorded_at >= cutoff)
        .order_by(ProbabilityHistory.recorded_at.asc())
    )
    result = await db.execute(query)
    records = result.scalars().all()

    points = [
        ProbabilityHistoryPoint(
            date=r.recorded_at,
            probability=r.probability,
            volume=r.volume_24h,
        )
        for r in records
    ]

    serialized = [p.model_dump(mode="json") for p in points]
    await redis_conn.set(cache_key, json.dumps(serialized, default=str), ex=120)
    return points
