import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update

from app.database import async_session
from app.ingestion.registry import get_enabled_clients
from app.models.event import Event
from app.models.probability_history import ProbabilityHistory

logger = structlog.get_logger()


async def _poll_all_markets_async() -> dict:
    """Poll all enabled market clients for updated prices."""
    clients = get_enabled_clients()
    total_updated = 0

    async with async_session() as session:
        for client in clients:
            source_name = client.__class__.__name__
            try:
                # Get all active events for this source
                result = await session.execute(
                    select(Event).where(
                        Event.source == source_name.replace("Client", "").lower(),
                        Event.status == "active",
                    )
                )
                events = result.scalars().all()

                for event in events:
                    try:
                        prices = await client.fetch_prices(event.source_id)
                        if not prices:
                            continue

                        latest = prices[-1]
                        new_prob = latest.get("probability", event.current_probability)

                        # Update event's current probability
                        await session.execute(
                            update(Event)
                            .where(Event.id == event.id)
                            .values(
                                current_probability=new_prob,
                                updated_at=datetime.now(timezone.utc),
                            )
                        )

                        # Insert new history record
                        history_record = ProbabilityHistory(
                            event_id=event.id,
                            probability=new_prob,
                            source_bid=latest.get("source_bid"),
                            source_ask=latest.get("source_ask"),
                            volume_24h=latest.get("volume_24h"),
                            recorded_at=datetime.now(timezone.utc),
                        )
                        session.add(history_record)
                        total_updated += 1

                    except Exception as exc:
                        await logger.awarning(
                            "Failed to poll event",
                            source=source_name,
                            event_id=str(event.id),
                            error=str(exc),
                        )

                await session.commit()
                await logger.ainfo(
                    "Polled market source",
                    source=source_name,
                    events_count=len(events),
                )

            except Exception as exc:
                await logger.aerror(
                    "Failed to poll market source",
                    source=source_name,
                    error=str(exc),
                )

    return {"updated": total_updated}


try:
    from celery_app import celery

    @celery.task(name="app.tasks.polling.poll_all_markets")
    def poll_all_markets() -> dict:
        """Celery task to poll all prediction market APIs for updated prices."""
        return asyncio.run(_poll_all_markets_async())

except ImportError:
    pass
