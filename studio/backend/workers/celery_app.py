from celery import Celery

from backend.core.config import settings

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
)

celery_app.autodiscover_tasks(["backend.workers"])
