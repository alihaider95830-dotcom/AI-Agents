import redis
import redis.asyncio as aioredis

from backend.core.config import settings

_sync_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)

_async_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_sync_redis() -> redis.Redis:
    """Get a synchronous Redis client using the module connection pool."""
    return redis.Redis(connection_pool=_sync_pool)


def get_async_redis() -> aioredis.Redis:
    """Get an asynchronous Redis client using the module connection pool."""
    return aioredis.Redis(connection_pool=_async_pool)


async def close_pools() -> None:
    """Close all Redis connection pools. Call this on application shutdown."""
    _sync_pool.disconnect()
    await _async_pool.disconnect()
