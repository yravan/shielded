import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.database import async_session
from app.ingestion.registry import get_enabled_clients
from app.models.event import Event

logger = structlog.get_logger()


async def _discover_new_events_async() -> dict:
    """Discover and insert new events from all enabled market clients."""
    clients = get_enabled_clients()
    total_new = 0

    async with async_session() as session:
        for client in clients:
            source_name = client.__class__.__name__
            try:
                raw_events = await client.fetch_events()
                await logger.ainfo(
                    "Discovered raw events",
                    source=source_name,
                    count=len(raw_events),
                )

                for raw in raw_events:
                    source = raw.get("source", "unknown")
                    source_id = raw.get("source_id", "")

                    if not source_id:
                        continue

                    # Check if event already exists
                    result = await session.execute(
                        select(Event).where(
                            Event.source == source,
                            Event.source_id == source_id,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update probability if changed
                        new_prob = raw.get("current_probability", existing.current_probability)
                        if abs(new_prob - existing.current_probability) > 0.001:
                            existing.current_probability = new_prob
                            existing.updated_at = datetime.now(timezone.utc)
                        continue

                    # Parse resolution date
                    resolution_date = raw.get("resolution_date")
                    if isinstance(resolution_date, str) and resolution_date:
                        try:
                            resolution_date = datetime.fromisoformat(
                                resolution_date.replace("Z", "+00:00")
                            )
                        except (ValueError, TypeError):
                            resolution_date = None

                    event = Event(
                        id=uuid.uuid4(),
                        title=raw["title"][:500],
                        description=raw.get("description", raw["title"]),
                        category=raw.get("category", "geopolitical"),
                        region=raw.get("region", "Global"),
                        source=source,
                        source_id=source_id,
                        source_url=raw.get("source_url", ""),
                        current_probability=raw.get("current_probability", 0.5),
                        resolution_date=resolution_date,
                        status="active",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(event)
                    total_new += 1

                await session.commit()

            except Exception as exc:
                await logger.aerror(
                    "Failed to discover events from source",
                    source=source_name,
                    error=str(exc),
                )

    await logger.ainfo("Discovery complete", new_events=total_new)
    return {"new_events": total_new}


try:
    from celery_app import celery

    @celery.task(name="app.tasks.discovery.discover_new_events")
    def discover_new_events() -> dict:
        """Celery task to discover new events from all prediction market platforms."""
        return asyncio.run(_discover_new_events_async())

except ImportError:
    pass
