import asyncio
from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select, update

from app.cache import EventCache
from app.config import settings
from app.database import async_session
from app.ingestion.registry import get_client_for_source
from app.models.event import Event
from app.models.user_tracked_event import UserTrackedEvent
from celery_app import celery

logger = structlog.get_logger()


async def _poll_all_markets_async() -> dict:
    """Poll all sources for updated prices.

    1. Read cached event lists from Redis
    2. Re-fetch current prices from APIs
    3. Update Redis cache with fresh prices
    4. Only update Postgres for tracked events
    """
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    cache = EventCache(redis)
    total_updated = 0

    async with async_session() as session:
        # Get set of tracked event source_ids for Postgres updates
        tracked_result = await session.execute(
            select(Event.source, Event.source_id, Event.id, Event.current_probability)
            .join(UserTrackedEvent, UserTrackedEvent.event_id == Event.id)
            .where(Event.status == "active", Event.is_parent == False)
        )
        tracked_events = {
            (row.source, row.source_id): (row.id, row.current_probability)
            for row in tracked_result.all()
        }

        for source in ("polymarket", "kalshi", "metaculus"):
            client = get_client_for_source(source)
            if not client:
                continue

            # Read cached events from Redis
            cached_events = await cache.get_all_events(source)
            if not cached_events:
                await logger.ainfo("No cached events for source, skipping poll", source=source)
                await client.close()
                continue

            # Collect non-parent events that need price updates
            events_to_poll = [
                e for e in cached_events if not e.is_parent
            ]

            for event in events_to_poll:
                try:
                    prices = await client.fetch_prices(event.source_id)
                    if not prices:
                        continue

                    # Cache the price history
                    await cache.set_history(source, event.source_id, prices)

                    # Update Postgres only for tracked events
                    key = (source, event.source_id)
                    if key in tracked_events:
                        db_id, old_prob = tracked_events[key]
                        new_prob = prices[-1].probability
                        if abs(new_prob - old_prob) > 0.001:
                            await session.execute(
                                update(Event)
                                .where(Event.id == db_id)
                                .values(
                                    previous_probability=old_prob,
                                    current_probability=new_prob,
                                    updated_at=datetime.now(timezone.utc),
                                )
                            )
                            total_updated += 1

                except Exception as exc:
                    await logger.awarning(
                        "Failed to poll event",
                        source=source,
                        source_id=event.source_id,
                        error=str(exc),
                    )

            await session.commit()
            await client.close()
            await logger.ainfo("Polled source", source=source, events=len(events_to_poll))

    await redis.aclose()
    return {"updated": total_updated}


@celery.task(name="app.tasks.polling.poll_all_markets")
def poll_all_markets() -> dict:
    """Celery task to poll all prediction market APIs for updated prices."""
    return asyncio.run(_poll_all_markets_async())
