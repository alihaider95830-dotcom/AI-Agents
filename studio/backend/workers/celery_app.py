from celery import Celery
from celery.schedules import crontab

from backend.core.config import settings

VECTOR_STORE_CLEANUP_TASK_NAME = "cleanup_vector_stores"
VECTOR_STORE_CLEANUP_SCHEDULE_NAME = "cleanup-vector-stores-daily"
VECTOR_STORE_CLEANUP_SCHEDULE_HOUR = 3
VECTOR_STORE_CLEANUP_SCHEDULE_MINUTE = 0
VECTOR_STORE_CLEANUP_IMPORT_PATH = "backend.tools.cleanup"

celery_app = Celery(
    "studio",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_backend=settings.redis_url,
    broker_url=settings.redis_url,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_default_queue=settings.celery_queue_name,
    task_routes={"backend.workers.tasks.*": {"queue": settings.celery_queue_name}},
    task_ignore_result=False,
    imports=(VECTOR_STORE_CLEANUP_IMPORT_PATH,),
    beat_schedule={
        VECTOR_STORE_CLEANUP_SCHEDULE_NAME: {
            "task": VECTOR_STORE_CLEANUP_TASK_NAME,
            "schedule": crontab(
                hour=VECTOR_STORE_CLEANUP_SCHEDULE_HOUR,
                minute=VECTOR_STORE_CLEANUP_SCHEDULE_MINUTE,
            ),
        }
    },
)

celery_app.autodiscover_tasks(["backend.workers"])
