from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery("shielded", broker=settings.CELERY_BROKER_URL)

celery.conf.beat_schedule = {
    "poll-markets": {
        "task": "app.tasks.polling.poll_all_markets",
        "schedule": settings.POLL_INTERVAL_SECONDS,
    },
    "discover-events": {
        "task": "app.tasks.discovery.discover_new_events",
        "schedule": crontab(minute=0),
    },
    "recompute-hedges": {
        "task": "app.tasks.hedges.recompute_hedges",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.autodiscover_tasks(["app.tasks"])
