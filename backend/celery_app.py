import os
import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready

from app.config import settings

_log = logging.getLogger(__name__)
_log.info(
    "Celery startup: broker=%s REDIS_URL=%s RAILWAY_ENV=%s",
    settings.CELERY_BROKER_URL,
    settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL,
    os.environ.get("RAILWAY_ENVIRONMENT", "<unset>"),
)

celery = Celery(
    "shielded",
    broker=settings.CELERY_BROKER_URL,
    include=[
        "app.tasks.polling",
        "app.tasks.discovery",
        "app.tasks.hedges",
        "app.tasks.risk_scoring",
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

# Risk scoring runs 15 min after discovery (which runs at :00)
beat_schedule["risk-scoring"] = {
    "task": "app.tasks.risk_scoring.run_risk_scoring",
    "schedule": crontab(minute=15),
}

# Hedge recomputation always runs (uses seeded data too)
beat_schedule["recompute-hedges"] = {
    "task": "app.tasks.hedges.recompute_hedges",
    "schedule": crontab(minute=0, hour="*/6"),
}

celery.conf.beat_schedule = beat_schedule
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"


@worker_ready.connect
def warmup_cache_on_startup(**kwargs):
    """Trigger a discovery run on worker startup to populate Redis cache."""
    celery.send_task("app.tasks.discovery.discover_new_events", countdown=30)
