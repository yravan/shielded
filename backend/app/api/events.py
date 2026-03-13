import json
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, RedisConn
from app.api.users import get_or_create_user
from app.auth import get_current_user, security
from app.ingestion.registry import get_enabled_clients
from app.models.event import Event
from app.models.user_tracked_event import UserTrackedEvent
from app.schemas.event import (
    ChildHistoryOut,
    ChildrenHistoryResponse,
    EventListResponse,
    EventOut,
    ProbabilityHistoryPoint,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["events"])


# ---------- Explore: browse ALL events ----------


@router.get("/explore/events", response_model=EventListResponse)
async def explore_events(
    db: DbSession,
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
    search: str | None = Query(None, description="Search title/description"),
    category: str | None = Query(None, description="Filter by category"),
    region: str | None = Query(None, description="Filter by region"),
    status: str | None = Query("active", description="Filter by status"),
    sort: str | None = Query("updated", description="Sort: updated, probability, created"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Browse all events in the system with search/filter/pagination.

    Only shows parent events and flat (non-child) events.
    Parent events include eagerly-loaded children.
    """
    db_user = await get_or_create_user(db, user)

    query = select(Event).where(Event.parent_event_id == None).options(selectinload(Event.children))  # noqa: E711
    count_query = select(func.count(Event.id)).where(Event.parent_event_id == None)  # noqa: E711

    if search:
        pattern = f"%{search}%"
        query = query.where(Event.title.ilike(pattern) | Event.description.ilike(pattern))
        count_query = count_query.where(
            Event.title.ilike(pattern) | Event.description.ilike(pattern)
        )
    if category:
        query = query.where(Event.category == category)
        count_query = count_query.where(Event.category == category)
    if region:
        query = query.where(Event.region == region)
        count_query = count_query.where(Event.region == region)
    if status:
        query = query.where(Event.status == status)
        count_query = count_query.where(Event.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    if sort == "probability":
        query = query.order_by(Event.current_probability.desc())
    elif sort == "created":
        query = query.order_by(Event.created_at.desc())
    else:
        query = query.order_by(Event.updated_at.desc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    events = result.scalars().all()

    # Get user's tracked event IDs for is_tracked flag
    tracked_result = await db.execute(
        select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
    )
    tracked_ids = {row[0] for row in tracked_result.all()}

    items = []
    for e in events:
        event_out = EventOut.model_validate(e)
        event_out.is_tracked = e.id in tracked_ids
        # For parent events, include children with tracking status
        if e.is_parent and e.children:
            children_out = []
            for child in e.children:
                child_out = EventOut.model_validate(child)
                child_out.is_tracked = child.id in tracked_ids
                child_out.parent_title = e.title
                children_out.append(child_out)
            # Sort children by probability descending
            children_out.sort(key=lambda c: c.current_probability, reverse=True)
            event_out.children = children_out
        items.append(event_out)

    return EventListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ---------- User's tracked events ----------


@router.get("/events", response_model=EventListResponse)
async def list_events(
    db: DbSession,
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query("active", description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    all: bool = Query(False, description="If true, return all events (legacy behavior)"),
):
    """List events. By default returns only user's tracked events.
    Pass all=true for legacy behavior (all events)."""
    if all:
        # Legacy behavior: return all events
        return await _list_all_events(db, redis_conn, category, status, page, page_size)

    db_user = await get_or_create_user(db, user)

    # Get tracked event IDs
    tracked_q = select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
    tracked_result = await db.execute(tracked_q)
    tracked_ids = [row[0] for row in tracked_result.all()]

    if not tracked_ids:
        return EventListResponse(items=[], total=0, page=1, page_size=page_size, pages=0)

    query = select(Event).where(Event.id.in_(tracked_ids)).options(selectinload(Event.children))
    count_query = select(func.count(Event.id)).where(Event.id.in_(tracked_ids))

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

    items = [EventOut.model_validate(e) for e in events]
    for item in items:
        item.is_tracked = True

    return EventListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


async def _list_all_events(db, redis_conn, category, status, page, page_size):
    """Legacy: return all events without user scoping."""
    cache_key = f"events:list:{category}:{status}:{page}:{page_size}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(Event).options(selectinload(Event.children))
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


# ---------- Track / Untrack ----------


@router.post("/events/{event_id}/track")
async def track_event(
    event_id: UUID,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Add an event to the user's tracked list."""
    db_user = await get_or_create_user(db, user)

    # Verify event exists and is not a parent container
    event_result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.is_parent:
        raise HTTPException(
            status_code=400,
            detail="Cannot track a parent event. Track individual markets instead.",
        )

    # Check if already tracked
    existing = await db.execute(
        select(UserTrackedEvent).where(
            UserTrackedEvent.user_id == db_user.id,
            UserTrackedEvent.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_tracked"}

    tracking = UserTrackedEvent(user_id=db_user.id, event_id=event_id)
    db.add(tracking)
    await db.flush()
    return {"status": "tracked"}


@router.delete("/events/{event_id}/track")
async def untrack_event(
    event_id: UUID,
    db: DbSession,
    user: dict = Depends(get_current_user),
):
    """Remove an event from the user's tracked list."""
    db_user = await get_or_create_user(db, user)

    result = await db.execute(
        select(UserTrackedEvent).where(
            UserTrackedEvent.user_id == db_user.id,
            UserTrackedEvent.event_id == event_id,
        )
    )
    tracking = result.scalar_one_or_none()
    if not tracking:
        raise HTTPException(status_code=404, detail="Event not tracked")

    await db.delete(tracking)
    await db.flush()
    return {"status": "untracked"}


# ---------- Single event & history ----------


async def _get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """Like get_current_user but returns None instead of 401 when unauthenticated."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event(
    event_id: UUID,
    db: DbSession,
    user: dict | None = Depends(_get_optional_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id).options(selectinload(Event.children)))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event_out = EventOut.model_validate(event)

    # If this is a child event, populate parent_title and load siblings
    if event.parent_event_id:
        parent_result = await db.execute(
            select(Event).where(Event.id == event.parent_event_id).options(selectinload(Event.children))
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            event_out.parent_title = parent.title
            # Load siblings (other children of the same parent)
            siblings = [
                EventOut.model_validate(c)
                for c in (parent.children or [])
                if c.id != event.id
            ]
            siblings.sort(key=lambda s: s.current_probability, reverse=True)
            event_out.children = siblings  # reuse children field for siblings

    # If this is a parent event, populate children sorted by probability
    if event.is_parent and event.children:
        children_out = [EventOut.model_validate(c) for c in event.children]
        children_out.sort(key=lambda c: c.current_probability, reverse=True)
        event_out.children = children_out

    # Check if the current user is tracking this event
    if user:
        db_user = await get_or_create_user(db, user)
        tracked = await db.execute(
            select(UserTrackedEvent.id).where(
                UserTrackedEvent.user_id == db_user.id,
                UserTrackedEvent.event_id == event_id,
            )
        )
        event_out.is_tracked = tracked.scalar_one_or_none() is not None

    return event_out


def _get_client_for_source(source: str):
    """Return the matching market client for a given source name."""
    clients = get_enabled_clients()
    for client in clients:
        client_source = client.__class__.__name__.replace("Client", "").lower()
        if client_source == source:
            return client
    return None


@router.get("/events/{event_id}/history", response_model=list[ProbabilityHistoryPoint])
async def get_event_history(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    hours: int = Query(2160, ge=1, le=8760, description="Hours of history to return"),
):
    cache_key = f"events:history:{event_id}:{hours}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    # Load event to get source info
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Fetch from source API
    client = _get_client_for_source(event.source)
    if not client:
        await logger.awarning(
            "No client found for event source", source=event.source, event_id=str(event_id)
        )
        return []

    try:
        raw_prices = await client.fetch_prices(event.source_id)
    except Exception:
        await logger.aerror(
            "Exception fetching prices from source",
            source=event.source,
            source_id=event.source_id,
            event_id=str(event_id),
        )
        return []

    if not raw_prices:
        await logger.awarning(
            "Source returned empty price history",
            source=event.source,
            source_id=event.source_id,
            event_id=str(event_id),
        )

    # Parse timestamps and filter by hours cutoff
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    points = []
    for point in raw_prices:
        recorded_at = point.get("recorded_at")
        if isinstance(recorded_at, (int, float)):
            recorded_at = datetime.fromtimestamp(recorded_at, tz=timezone.utc)
        elif isinstance(recorded_at, str):
            try:
                recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                recorded_at = datetime.now(timezone.utc)
        else:
            continue  # skip points without valid timestamps

        if recorded_at < cutoff:
            continue

        prob = point["probability"]
        # Filter out zero-probability points (empty candles) to prevent sawtooth
        if prob <= 0:
            continue

        points.append(
            ProbabilityHistoryPoint(
                date=recorded_at,
                probability=prob,
                volume=point.get("volume_24h"),
            )
        )

    serialized = [p.model_dump(mode="json") for p in points]
    await redis_conn.set(cache_key, json.dumps(serialized, default=str), ex=300)
    return points


# ---------- Parent event children history ----------


@router.get(
    "/events/{event_id}/children-history",
    response_model=ChildrenHistoryResponse,
)
async def get_children_history(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    hours: int = Query(2160, ge=1, le=8760, description="Hours of history"),
):
    """Fetch price history for all children of a parent event."""
    cache_key = f"events:children-history:{event_id}:{hours}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    # Load parent event
    result = await db.execute(select(Event).where(Event.id == event_id).options(selectinload(Event.children)))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Event not found")
    if not parent.is_parent:
        raise HTTPException(status_code=400, detail="Event is not a parent event")

    client = _get_client_for_source(parent.source)
    if not client:
        return ChildrenHistoryResponse(children={})

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    children_data: dict[str, ChildHistoryOut] = {}

    # Fetch history for each child (top 10 by probability to limit API calls)
    children = sorted(
        parent.children or [],
        key=lambda c: c.current_probability,
        reverse=True,
    )[:10]

    for child in children:
        try:
            raw_prices = await client.fetch_prices(child.source_id)
        except Exception:
            await logger.awarning(
                "Failed to fetch child history",
                child_id=str(child.id),
                source_id=child.source_id,
            )
            continue

        points = []
        for point in raw_prices:
            recorded_at = point.get("recorded_at")
            if isinstance(recorded_at, (int, float)):
                recorded_at = datetime.fromtimestamp(recorded_at, tz=timezone.utc)
            elif isinstance(recorded_at, str):
                try:
                    recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
            else:
                continue

            if recorded_at < cutoff:
                continue

            prob = point["probability"]
            if prob <= 0:
                continue

            points.append(
                ProbabilityHistoryPoint(
                    date=recorded_at,
                    probability=prob,
                    volume=point.get("volume_24h"),
                )
            )

        children_data[str(child.id)] = ChildHistoryOut(
            title=child.title,
            history=points,
        )

    response = ChildrenHistoryResponse(children=children_data)
    await redis_conn.set(
        cache_key,
        response.model_dump_json(),
        ex=300,
    )
    return response
