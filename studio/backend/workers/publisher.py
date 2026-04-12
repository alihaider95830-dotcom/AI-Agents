import json

import redis

from backend.core.event_store import append_event
from backend.core.logging import get_logger
from backend.core.redis_client import get_sync_redis

logger = get_logger(__name__)


def publish_event(job_id: str, payload: dict) -> None:
    try:
        # Save to event log for replay mechanism
        append_event(job_id, payload)
        
        # Publish to live subscribers
        client = get_sync_redis()
        client.publish(f"job:{job_id}", json.dumps(payload))
    except redis.RedisError as exc:
        logger.warning("failed to publish job event: %s", exc)

