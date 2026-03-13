import asyncio
import json
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, RedisConn
from app.api.users import get_or_create_user
from app.auth import get_current_user, security
from app.cache import EventCache
from app.ingestion.base import PricePoint
from app.ingestion.registry import get_client_for_source
from app.models.event import Event
from app.models.user_tracked_event import UserTrackedEvent
from app.models.company import Company
from app.models.exposure import Exposure
from app.risk_engine import (
    estimate_impact_pcts,
    match_event_to_companies,
    score_event_for_company,
)
from app.schemas.event import (
    ChildHistoryOut,
    ChildrenHistoryResponse,
    EventListResponse,
    EventOut,
    ProbabilityHistoryPoint,
    SuggestedEventOut,
)
from app.services.risk_service import (
    company_to_input,
    event_to_input,
    theme_to_exposure_type,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["events"])


# ---------- Helpers ----------


async def _get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """Like get_current_user but returns None instead of 401 when unauthenticated."""
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def _parse_resolution_date(val: str | None) -> datetime | None:
    """Parse an ISO 8601 resolution date string to datetime."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _price_points_to_history(
    points: list[PricePoint], cutoff: datetime
) -> list[ProbabilityHistoryPoint]:
    """Convert PricePoints to ProbabilityHistoryPoints, filtering by cutoff."""
    result = []
    for p in points:
        dt = datetime.fromtimestamp(p.timestamp, tz=timezone.utc)
        if dt < cutoff:
            continue
        if p.probability <= 0:
            continue
        result.append(ProbabilityHistoryPoint(
            date=dt,
            probability=p.probability,
            volume=p.volume,
        ))
    return result


# ---------- Explore: browse ALL events (Redis-first) ----------


@router.get("/explore/events", response_model=EventListResponse)
async def explore_events(
    db: DbSession,
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
    search: str | None = Query(None, description="Search title/description"),
    category: str | None = Query(None, description="Filter by category"),
    region: str | None = Query(None, description="Filter by region"),
    source: str | None = Query(None, description="Filter by source (polymarket, kalshi)"),
    status: str | None = Query("active", description="Filter by status"),
    sort: str | None = Query("updated", description="Sort: updated, probability, created"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Browse all events with search/filter/pagination.

    Reads from Redis cache first; falls back to Postgres.
    Only shows parent events and flat (non-child) events.
    """
    cache = EventCache(redis_conn)

    # Check short-lived explore cache
    cached = await cache.get_explore(search, category, region, status, sort, page, page_size)
    if cached:
        return json.loads(cached)

    # Try loading all events from Redis and filtering in Python
    all_normalized = []
    load_sources = [source] if source else ["polymarket", "kalshi", "metaculus"]
    for src in load_sources:
        events = await cache.get_all_events(src)
        if events:
            all_normalized.extend(events)

    if all_normalized:
        # Filter to parent + flat events only (skip children within parent.markets)
        child_source_ids = set()
        for e in all_normalized:
            if e.is_parent:
                for m in e.markets:
                    child_source_ids.add(m.source_id)
        top_level = [e for e in all_normalized if e.is_parent or e.source_id not in child_source_ids]

        if search:
            s = search.lower()
            top_level = [
                e for e in top_level if s in e.title.lower() or s in e.description.lower()
            ]
        if category:
            top_level = [e for e in top_level if e.category == category]
        if region:
            top_level = [e for e in top_level if e.region == region]
        if status:
            top_level = [e for e in top_level if e.status == status]

        # Sort
        if sort == "probability":
            top_level.sort(key=lambda e: e.probability, reverse=True)
        elif sort == "updated":
            # Shuffle to interleave Kalshi and Polymarket (no timestamps available)
            random.shuffle(top_level)

        total = len(top_level)
        start = (page - 1) * page_size
        page_items = top_level[start : start + page_size]

        # Get tracked IDs from Postgres for is_tracked flag
        db_user = await get_or_create_user(db, user)
        tracked_result = await db.execute(
            select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
        )
        tracked_ids = {row[0] for row in tracked_result.all()}

        # Map source_ids to DB IDs for tracking check
        source_ids = [e.source_id for e in page_items]
        for e in page_items:
            for m in e.markets:
                source_ids.append(m.source_id)

        db_result = await db.execute(
            select(Event.id, Event.source_id).where(Event.source_id.in_(source_ids))
        )
        source_id_to_db_id = {row.source_id: row.id for row in db_result.all()}

        items = []
        for ne in page_items:
            db_id = source_id_to_db_id.get(ne.source_id)
            event_out = EventOut(
                id=db_id or UUID(int=0),
                title=ne.title,
                description=ne.description,
                category=ne.category,
                region=ne.region,
                source=ne.source,
                source_id=ne.source_id,
                source_url=ne.source_url,
                current_probability=ne.probability,
                previous_probability=None,
                resolution_date=_parse_resolution_date(ne.resolution_date),
                status=ne.status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                is_parent=ne.is_parent,
                is_tracked=db_id in tracked_ids if db_id else False,
                expected_value=ne.expected_value,
                is_quantitative=ne.is_quantitative,
                image_url=ne.image_url,
                tags=ne.tags or None,
                volume=ne.volume,
            )

            # Populate children for parent events
            if ne.is_parent and ne.markets:
                children_out = []
                for m in ne.markets:
                    child_db_id = source_id_to_db_id.get(m.source_id)
                    children_out.append(EventOut(
                        id=child_db_id or UUID(int=0),
                        title=m.title,
                        description=ne.description,
                        category=ne.category,
                        region=ne.region,
                        source=ne.source,
                        source_id=m.source_id,
                        source_url=ne.source_url,
                        current_probability=m.probability,
                        status=ne.status,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                        is_parent=False,
                        is_tracked=child_db_id in tracked_ids if child_db_id else False,
                        parent_title=ne.title,
                        image_url=m.image_url,
                        volume=m.volume,
                        resolution_date=_parse_resolution_date(ne.resolution_date),
                    ))
                children_out.sort(key=lambda c: c.current_probability, reverse=True)
                event_out.children = children_out

            items.append(event_out)

        response = EventListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0,
        )
        await cache.set_explore(
            search, category, region, status, sort, page, page_size,
            response.model_dump_json(),
        )
        return response

    # Fallback to Postgres
    return await _explore_from_postgres(db, user, search, category, region, status, sort, page, page_size)


async def _explore_from_postgres(db, user, search, category, region, status, sort, page, page_size):
    """Fallback: browse events from Postgres."""
    db_user = await get_or_create_user(db, user)

    query = (
        select(Event)
        .where(Event.parent_event_id == None)  # noqa: E711
        .options(selectinload(Event.children))
    )
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

    tracked_result = await db.execute(
        select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
    )
    tracked_ids = {row[0] for row in tracked_result.all()}

    items = []
    for e in events:
        event_out = EventOut.model_validate(e)
        event_out.is_tracked = e.id in tracked_ids
        if e.is_parent and e.children:
            children_out = []
            for child in e.children:
                child_out = EventOut.model_validate(child)
                child_out.is_tracked = child.id in tracked_ids
                child_out.parent_title = e.title
                children_out.append(child_out)
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


# ---------- Suggested events ----------


@router.get("/events/suggestions", response_model=list[SuggestedEventOut])
async def get_suggested_events(
    db: DbSession,
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50),
):
    """Return events the user should consider tracking, computed on-the-fly.

    Runs the risk engine against the user's companies and active untracked
    events. Results are cached in Redis for 5 minutes.
    """
    db_user = await get_or_create_user(db, user)

    # Check Redis cache
    cache_key = f"suggestions:{db_user.id}:{limit}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    # Get user's companies with risk profiles
    company_result = await db.execute(
        select(Company).where(Company.user_id == db_user.id)
    )
    companies = company_result.scalars().all()
    companies_with_profiles = [c for c in companies if c.risk_profile]
    if not companies_with_profiles:
        return []

    company_map = {str(c.id): c for c in companies_with_profiles}
    company_inputs = [company_to_input(c) for c in companies_with_profiles]

    # Get already-tracked event IDs
    tracked_result = await db.execute(
        select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
    )
    tracked_ids = {row[0] for row in tracked_result.all()}

    # Load active non-parent events, excluding already tracked
    event_query = select(Event).where(
        Event.status == "active",
        Event.is_parent == False,  # noqa: E712
    )
    event_result = await db.execute(event_query)
    events = event_result.scalars().all()
    untracked_events = [e for e in events if e.id not in tracked_ids]

    # Pre-load parent titles for child events
    parent_ids = {e.parent_event_id for e in untracked_events if e.parent_event_id}
    parent_title_map: dict[UUID, str] = {}
    if parent_ids:
        parent_result = await db.execute(
            select(Event.id, Event.title).where(Event.id.in_(parent_ids))
        )
        parent_title_map = {row[0]: row[1] for row in parent_result.all()}

    # Run risk engine matching on-the-fly, grouping by parent event
    seen_events: dict[UUID, SuggestedEventOut] = {}
    for event in untracked_events:
        event_input = event_to_input(event)
        matches = match_event_to_companies(event_input, company_inputs, min_score=20)

        for company_id, match in matches:
            group_key = event.parent_event_id or event.id

            if group_key in seen_events:
                if match.relevance_score <= seen_events[group_key].relevance_score:
                    continue

            company = company_map.get(company_id)
            if not company:
                continue

            # For child events with a parent, use parent title/id so one card per parent
            if event.parent_event_id:
                display_id = event.parent_event_id
                display_title = parent_title_map.get(event.parent_event_id, event.title)
            else:
                display_id = event.id
                display_title = event.title

            seen_events[group_key] = SuggestedEventOut(
                id=display_id,
                title=display_title,
                description=event.description or "",
                category=event.category or "",
                region=event.region or "",
                source=event.source or "",
                source_url=event.source_url or "",
                current_probability=event.current_probability,
                resolution_date=event.resolution_date,
                status=event.status,
                relevance_score=match.relevance_score,
                matched_company_name=company.name,
                matched_company_id=company.id,
                matched_themes=match.matched_themes,
                parent_event_id=event.parent_event_id,
                parent_title=parent_title_map.get(event.parent_event_id) if event.parent_event_id else None,
                image_url=event.image_url,
                tags=event.tags,
            )

    suggestions = sorted(seen_events.values(), key=lambda s: s.relevance_score, reverse=True)
    result = suggestions[:limit]

    # Cache for 5 minutes
    from pydantic import TypeAdapter
    ta = TypeAdapter(list[SuggestedEventOut])
    await redis_conn.set(cache_key, ta.dump_json(result), ex=300)

    return result


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
        return await _list_all_events(db, redis_conn, category, status, page, page_size)

    db_user = await get_or_create_user(db, user)

    tracked_q = select(UserTrackedEvent.event_id).where(UserTrackedEvent.user_id == db_user.id)
    tracked_result = await db.execute(tracked_q)
    tracked_ids = [row[0] for row in tracked_result.all()]

    if not tracked_ids:
        return EventListResponse(items=[], total=0, page=1, page_size=page_size, pages=0)

    # Look up fresh data from Redis where possible, fall back to Postgres
    cache = EventCache(redis_conn)

    # Get DB events to map source info
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

    # Try to enrich from Redis cache
    items = []
    for e in events:
        cached_event = await cache.get_event(e.source, e.source_id)
        event_out = EventOut.model_validate(e)
        if cached_event:
            event_out.current_probability = cached_event.probability
            event_out.expected_value = cached_event.expected_value
            event_out.is_quantitative = cached_event.is_quantitative
        event_out.is_tracked = True
        items.append(event_out)

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
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
):
    """Add an event to the user's tracked list and create exposures for matching companies."""
    db_user = await get_or_create_user(db, user)

    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.is_parent:
        raise HTTPException(
            status_code=400,
            detail="Cannot track a parent event. Track individual markets instead.",
        )

    existing = await db.execute(
        select(UserTrackedEvent).where(
            UserTrackedEvent.user_id == db_user.id,
            UserTrackedEvent.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_tracked", "exposures_created": 0}

    tracking = UserTrackedEvent(user_id=db_user.id, event_id=event_id)
    db.add(tracking)

    # Create exposures for user's companies with risk profiles
    company_result = await db.execute(
        select(Company).where(Company.user_id == db_user.id)
    )
    companies = company_result.scalars().all()
    companies_with_profiles = [c for c in companies if c.risk_profile]

    exposures_created = 0
    event_input = event_to_input(event)

    for company in companies_with_profiles:
        company_input = company_to_input(company)
        match = score_event_for_company(event_input, company_input)

        if match.relevance_score >= 20:
            impact_pcts = estimate_impact_pcts(
                match.matched_themes,
                match.relevance_score,
            )
            primary_theme = match.matched_themes[0] if match.matched_themes else "geopolitical"
            exposure = Exposure(
                id=uuid.uuid4(),
                company_id=company.id,
                event_id=event_id,
                exposure_type=theme_to_exposure_type(primary_theme),
                exposure_direction="negative",
                sensitivity=match.relevance_score / 100.0,
                revenue_impact_pct=impact_pcts["revenue_impact_pct"],
                opex_impact_pct=impact_pcts["opex_impact_pct"],
                capex_impact_pct=impact_pcts["capex_impact_pct"],
                status="suggested",
                relevance_score=match.relevance_score,
                matched_themes=match.matched_themes,
                notes=match.explanation,
                created_at=datetime.now(timezone.utc),
            )
            db.add(exposure)
            exposures_created += 1

    await db.flush()

    # Clear Redis caches for affected companies so fresh data is fetched
    for company in companies_with_profiles:
        await redis_conn.delete(f"company-event-impacts:{company.id}")
        await redis_conn.delete(f"company:exposure:{company.id}")
        await redis_conn.delete(f"impact:{company.id}:{event_id}")
    # Clear suggestions cache for this user
    await redis_conn.delete(f"suggestions:{db_user.id}:{20}")

    return {"status": "tracked", "exposures_created": exposures_created}


@router.delete("/events/{event_id}/track")
async def untrack_event(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    user: dict = Depends(get_current_user),
):
    """Remove an event from the user's tracked list and delete associated exposures."""
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

    # Delete exposures for this event across user's companies
    company_result = await db.execute(
        select(Company.id).where(Company.user_id == db_user.id)
    )
    company_ids = [row[0] for row in company_result.all()]

    if company_ids:
        await db.execute(
            delete(Exposure).where(
                Exposure.event_id == event_id,
                Exposure.company_id.in_(company_ids),
            )
        )

    await db.flush()

    # Clear Redis caches for affected companies
    for cid in company_ids:
        await redis_conn.delete(f"company-event-impacts:{cid}")
        await redis_conn.delete(f"company:exposure:{cid}")
        await redis_conn.delete(f"impact:{cid}:{event_id}")
    await redis_conn.delete(f"suggestions:{db_user.id}:{20}")

    return {"status": "untracked"}


# ---------- Single event & history ----------


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    user: dict | None = Depends(_get_optional_user),
):
    """Get a single event. Looks up from Postgres, enriches with Redis live data."""
    result = await db.execute(
        select(Event).where(Event.id == event_id).options(selectinload(Event.children))
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    cache = EventCache(redis_conn)
    event_out = EventOut.model_validate(event)

    # Enrich with Redis live data
    cached = await cache.get_event(event.source, event.source_id)
    if cached:
        event_out.current_probability = cached.probability
        event_out.expected_value = cached.expected_value
        event_out.is_quantitative = cached.is_quantitative

    # If child, populate parent_title and siblings
    if event.parent_event_id:
        parent_result = await db.execute(
            select(Event)
            .where(Event.id == event.parent_event_id)
            .options(selectinload(Event.children))
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            event_out.parent_title = parent.title
            siblings = []
            for c in (parent.children or []):
                if c.id == event.id:
                    continue
                sib = EventOut.model_validate(c)
                cached_sib = await cache.get_event(c.source, c.source_id)
                if cached_sib:
                    sib.current_probability = cached_sib.probability
                siblings.append(sib)
            siblings.sort(key=lambda s: s.current_probability, reverse=True)
            event_out.children = siblings

    # If parent, populate children sorted by probability
    if event.is_parent and event.children:
        children_out = []
        for c in event.children:
            child_out = EventOut.model_validate(c)
            cached_child = await cache.get_event(c.source, c.source_id)
            if cached_child:
                child_out.current_probability = cached_child.probability
            children_out.append(child_out)
        children_out.sort(key=lambda c: c.current_probability, reverse=True)
        event_out.children = children_out

    # Check tracking status
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


@router.get("/events/{event_id}/history", response_model=list[ProbabilityHistoryPoint])
async def get_event_history(
    event_id: UUID,
    db: DbSession,
    redis_conn: RedisConn,
    hours: int = Query(2160, ge=1, le=8760, description="Hours of history to return"),
):
    """Fetch probability history. Redis cache first, then API fetch."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    cache = EventCache(redis_conn)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Check Redis cache (keyed by hours so different ranges are cached separately)
    cached_points = await cache.get_history(event.source, event.source_id, hours)
    if cached_points is not None:
        return _price_points_to_history(cached_points, cutoff)

    # Fetch from source API
    client = get_client_for_source(event.source)
    if not client:
        return []

    try:
        points = await client.fetch_prices(event.source_id, hours=hours, series_ticker=event.series_ticker)
    except Exception:
        await logger.aerror(
            "Failed to fetch prices", source=event.source, source_id=event.source_id
        )
        return []
    finally:
        await client.close()

    if points:
        await cache.set_history(event.source, event.source_id, points, hours)

    return _price_points_to_history(points, cutoff)


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
    """Fetch price history for all children of a parent event using asyncio.gather."""
    # Check response cache
    cache_key = f"events:children-history:{event_id}:{hours}"
    cached = await redis_conn.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(
        select(Event).where(Event.id == event_id).options(selectinload(Event.children))
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Event not found")
    if not parent.is_parent:
        raise HTTPException(status_code=400, detail="Event is not a parent event")

    client = get_client_for_source(parent.source)
    if not client:
        return ChildrenHistoryResponse(children={})

    cache = EventCache(redis_conn)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Top 10 children by probability
    children = sorted(
        parent.children or [],
        key=lambda c: c.current_probability,
        reverse=True,
    )[:10]

    async def _fetch_child(child: Event) -> tuple[str, ChildHistoryOut]:
        # Try cache first
        cached_pts = await cache.get_history(child.source, child.source_id, hours)
        if cached_pts is not None:
            points = cached_pts
        else:
            try:
                points = await client.fetch_prices(child.source_id, hours=hours, series_ticker=child.series_ticker)
                if points:
                    await cache.set_history(child.source, child.source_id, points, hours)
            except Exception:
                await logger.awarning(
                    "Failed to fetch child history", child_id=str(child.id)
                )
                points = []

        history = _price_points_to_history(points, cutoff)
        return str(child.id), ChildHistoryOut(title=child.title, history=history)

    # Fetch all children in parallel
    results = await asyncio.gather(*[_fetch_child(c) for c in children])
    await client.close()

    children_data = dict(results)
    response = ChildrenHistoryResponse(children=children_data)
    await redis_conn.set(cache_key, response.model_dump_json(), ex=300)
    return response
