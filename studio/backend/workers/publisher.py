import json

import redis

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

_pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def publish_event(job_id: str, payload: dict) -> None:
    try:
        client = redis.Redis(connection_pool=_pool)
        client.publish(f"job:{job_id}", json.dumps(payload))
    except redis.RedisError as exc:
        logger.warning("failed to publish job event: %s", exc)

