"""ReelIQ Backend — Celery Application Setup"""
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "reeliq",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.video_pipeline",
        "app.workers.analysis_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # Results expire after 1 hour
    broker_connection_retry_on_startup=True,
)
