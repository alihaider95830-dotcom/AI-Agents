from __future__ import annotations

import time
import uuid

from fastapi import HTTPException, Request
from redis.asyncio.client import Redis

GENERATE_RATE_LIMIT_REQUESTS = 10
GLOBAL_RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60
GENERATE_RATE_LIMIT_PREFIX = "rl:gen"
GLOBAL_RATE_LIMIT_PREFIX = "rl:global"
RATE_LIMIT_DETAIL = "Too many requests"


class RateLimiter:
    def __init__(self, requests: int, window_seconds: int, prefix: str = "rl"):
        self.requests = requests
        self.window_seconds = window_seconds
        self.prefix = prefix

    async def __call__(self, request: Request, redis: Redis) -> None:
        client_host = request.client.host if request.client else "unknown"
        key = f"{self.prefix}:{client_host}"
        now = time.time()
        window_start = now - self.window_seconds
        member = f"{now}:{uuid.uuid4().hex}"

        pipeline = redis.pipeline()
        pipeline.zremrangebyscore(key, "-inf", window_start)
        pipeline.zadd(key, {member: now})
        pipeline.zcard(key)
        pipeline.expire(key, self.window_seconds)

        results = await pipeline.execute()
        count = results[2]
        if count >= self.requests:
            raise HTTPException(
                status_code=429,
                detail=RATE_LIMIT_DETAIL,
                headers={"Retry-After": str(self.window_seconds)},
            )


generate_limiter = RateLimiter(
    requests=GENERATE_RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    prefix=GENERATE_RATE_LIMIT_PREFIX,
)
global_limiter = RateLimiter(
    requests=GLOBAL_RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    prefix=GLOBAL_RATE_LIMIT_PREFIX,
)
