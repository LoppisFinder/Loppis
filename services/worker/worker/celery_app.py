import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crawler"))

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("loppisfinder", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Stockholm",
    enable_utc=True,
    beat_schedule={
        "run-crawlers-hourly": {
            "task": "worker.tasks.run_crawlers",
            "schedule": crontab(minute=0),
        },
        "recompute-scores-nightly": {
            "task": "worker.tasks.recompute_all_scores",
            "schedule": crontab(hour=2, minute=0),
        },
        "process-alerts-every-15min": {
            "task": "worker.tasks.process_alerts",
            "schedule": crontab(minute="*/15"),
        },
        "purge-old-data-weekly": {
            "task": "worker.tasks.purge_old_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),
        },
    },
)

celery_app.autodiscover_tasks(["worker"], force=True)
import worker.tasks  # noqa: F401, E402
