import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select

from app.cache import EventCache
from app.config import settings
from app.database import async_session
from app.ingestion.base import NormalizedEvent
from app.ingestion.registry import get_enabled_clients
from app.models.event import Event
from celery_app import celery

logger = structlog.get_logger()


def _parse_resolution_date(raw_date) -> datetime | None:
    """Parse a resolution date string into a datetime object."""
    if isinstance(raw_date, str) and raw_date:
        try:
            return datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return raw_date if isinstance(raw_date, datetime) else None


async def _upsert_event_to_pg(
    session, event: NormalizedEvent, parent_db_id: uuid.UUID | None = None
) -> uuid.UUID:
    """Thin upsert into Postgres. Returns the DB id."""
    result = await session.execute(
        select(Event).where(Event.source == event.source, Event.source_id == event.source_id)
    )
    existing = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if existing:
        # Update mutable fields
        if not event.is_parent:
            new_prob = event.probability
            if abs(new_prob - existing.current_probability) > 0.001:
                existing.previous_probability = existing.current_probability
                existing.current_probability = new_prob
        existing.title = event.title[:500]
        existing.is_parent = event.is_parent
        existing.status = event.status
        existing.category = event.category
        existing.region = event.region
        existing.is_quantitative = event.is_quantitative
        existing.expected_value = event.expected_value
        existing.updated_at = now
        if event.image_url:
            existing.image_url = event.image_url
        if event.tags:
            existing.tags = event.tags
        if event.series_ticker:
            existing.series_ticker = event.series_ticker
        if event.volume is not None:
            existing.volume = event.volume
        if parent_db_id is not None:
            existing.parent_event_id = parent_db_id
        return existing.id

    resolution_date = _parse_resolution_date(event.resolution_date)
    db_event = Event(
        id=uuid.uuid4(),
        title=event.title[:500],
        description=event.description,
        category=event.category,
        region=event.region,
        source=event.source,
        source_id=event.source_id,
        source_url=event.source_url,
        current_probability=event.probability,
        resolution_date=resolution_date,
        status=event.status,
        is_parent=event.is_parent,
        parent_event_id=parent_db_id,
        is_quantitative=event.is_quantitative,
        expected_value=event.expected_value,
        image_url=event.image_url,
        tags=event.tags or [],
        series_ticker=event.series_ticker,
        volume=event.volume,
        created_at=now,
        updated_at=now,
    )
    session.add(db_event)
    await session.flush()
    return db_event.id


async def _run_ev_computation(event: NormalizedEvent, client=None) -> None:
    """Set EV fields in-place. Currently a no-op for Kalshi.

    Forecast percentile fetching removed — returns 400 for all numeric-strike
    events with mutually_exclusive=False. Polymarket EV is set during ingestion.
    """
    if not event.markets or len(event.markets) < 2:
        return


async def _discover_new_events_async() -> dict:
    """Discover and insert new events from all enabled market clients."""
    clients = get_enabled_clients()
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    cache = EventCache(redis)
    total_new = 0
    seen_keys: dict[str, set[str]] = {}  # source -> set of source_ids still active

    for client in clients:
        source = client.source_name
        seen_keys[source] = set()
        try:
            all_events = await client.fetch_all_events()
            await logger.ainfo("Discovered events", source=source, count=len(all_events))

            # Run EV computation on multi-market events
            for event in all_events:
                await _run_ev_computation(event, client=client)

            # Filter expired/resolved child markets from parent events
            for event in all_events:
                if event.is_parent and event.markets:
                    event.markets = [
                        m for m in event.markets
                        if not m.is_closed and m.probability < 0.99
                    ]

            # Thin upsert into Postgres (fresh session per source)
            async with async_session() as session:
                for event in all_events:
                    seen_keys[source].add(event.source_id)

                    if event.is_parent and event.markets:
                        parent_db_id = await _upsert_event_to_pg(session, event)
                        for market in event.markets:
                            child_event = NormalizedEvent(
                                source=event.source,
                                source_id=market.source_id,
                                source_url=event.source_url,
                                title=market.title,
                                description=event.description,
                                category=event.category,
                                region=event.region,
                                status="closed" if market.is_closed else event.status,
                                resolution_date=event.resolution_date,
                                probability=market.probability,
                                is_parent=False,
                                image_url=market.image_url or event.image_url,
                                tags=event.tags,
                                series_ticker=market.series_ticker or event.series_ticker,
                                volume=market.volume,
                            )
                            seen_keys[source].add(market.source_id)
                            await _upsert_event_to_pg(session, child_event, parent_db_id)
                    else:
                        await _upsert_event_to_pg(session, event)

                await session.commit()

            # Store in Redis AFTER Postgres commit so explore endpoint
            # never exposes events that don't exist in the DB yet
            await cache.set_all_events(source, all_events)

        except Exception as exc:
            await logger.aerror(
                "Failed to discover events", source=source, error=str(exc)
            )
        finally:
            await client.close()

    # Mark events no longer returned by APIs as expired
    async with async_session() as session:
        for source, active_ids in seen_keys.items():
            if not active_ids:
                continue
            result = await session.execute(
                select(Event).where(
                    Event.source == source,
                    Event.status == "active",
                )
            )
            db_events = result.scalars().all()
            expired_count = 0
            for db_event in db_events:
                if db_event.source_id not in active_ids:
                    db_event.status = "expired"
                    db_event.updated_at = datetime.now(timezone.utc)
                    expired_count += 1
            if expired_count:
                await session.commit()
                await logger.ainfo(
                    "Marked events as expired", source=source, count=expired_count
                )

    await redis.aclose()
    await logger.ainfo("Discovery complete", new_events=total_new)
    return {"status": "ok"}


@celery.task(name="app.tasks.discovery.discover_new_events")
def discover_new_events() -> dict:
    """Celery task to discover new events from all prediction market platforms."""
    from app.database import engine
    asyncio.run(engine.dispose())
    result = asyncio.run(_discover_new_events_async())
    # Chain: run risk scoring after new events are discovered
    from app.tasks.risk_scoring import run_risk_scoring

    run_risk_scoring.delay()
    return result
