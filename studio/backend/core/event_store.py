import json

from backend.core.config import settings
from backend.core.redis_client import get_async_redis, get_sync_redis

EVENT_KEY_PREFIX = "events:"


def append_event(job_id: str, payload: dict) -> None:
    """Append a JSON event to the Redis list synchronously (for Celery)."""
    client = get_sync_redis()
    key = f"{EVENT_KEY_PREFIX}{job_id}"
    value = json.dumps(payload)
    
    pipeline = client.pipeline()
    pipeline.rpush(key, value)
    pipeline.expire(key, settings.event_store_ttl_seconds)
    pipeline.execute()


def get_events(job_id: str, from_index: int = 0) -> list[dict]:
    """Get events from the Redis list synchronously, starting at index."""
    client = get_sync_redis()
    key = f"{EVENT_KEY_PREFIX}{job_id}"
    raw_events = client.lrange(key, from_index, -1)
    return [json.loads(e) for e in raw_events]


async def async_append_event(job_id: str, payload: dict) -> None:
    """Append a JSON event to the Redis list asynchronously."""
    client = get_async_redis()
    key = f"{EVENT_KEY_PREFIX}{job_id}"
    value = json.dumps(payload)
    
    pipeline = client.pipeline()
    pipeline.rpush(key, value)
    pipeline.expire(key, settings.event_store_ttl_seconds)
    await pipeline.execute()


async def async_get_events(job_id: str, from_index: int = 0) -> list[dict]:
    """Get events from the Redis list asynchronously, starting at index."""
    client = get_async_redis()
    key = f"{EVENT_KEY_PREFIX}{job_id}"
    raw_events = await client.lrange(key, from_index, -1)
    return [json.loads(e) for e in raw_events]
