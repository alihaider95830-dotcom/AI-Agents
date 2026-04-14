from fastapi import Depends, Request
from redis.asyncio.client import Redis

from backend.core.auth import get_current_user
from backend.core.exceptions import ForbiddenError
from backend.core.rate_limit import generate_limiter, global_limiter
from backend.core.redis_client import get_async_redis
from backend.db.models import User
from backend.db.session import get_db


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user.

    ``get_current_user`` auto-provisions users on first login, so *user*
    should never be ``None``.  This guard is kept as a safety net in case
    the upstream dependency is swapped or modified.
    """
    if user is None:
        raise ForbiddenError("User is not active")
    return user


async def get_redis() -> Redis:
    return get_async_redis()


async def rate_limit_generate(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    await generate_limiter(request, redis)


async def rate_limit_global(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    await global_limiter(request, redis)
