from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery(
    "shielded",
    broker=settings.CELERY_BROKER_URL,
    include=[
        "app.tasks.polling",
        "app.tasks.discovery",
        "app.tasks.hedges",
    ],
)

beat_schedule: dict = {}

if settings.ENABLE_LIVE_POLLING:
    beat_schedule["poll-markets"] = {
        "task": "app.tasks.polling.poll_all_markets",
        "schedule": settings.POLL_INTERVAL_SECONDS,
    }
    beat_schedule["discover-events"] = {
        "task": "app.tasks.discovery.discover_new_events",
        "schedule": crontab(minute=0),
    }

# Hedge recomputation always runs (uses seeded data too)
beat_schedule["recompute-hedges"] = {
    "task": "app.tasks.hedges.recompute_hedges",
    "schedule": crontab(minute=0, hour="*/6"),
}

celery.conf.beat_schedule = beat_schedule
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
