from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from backend.core.rate_limit import RATE_LIMIT_WINDOW_SECONDS, RateLimiter

TEST_RATE_LIMIT = 10
TEST_RATE_LIMIT_PREFIX = "rl:test"


def make_pipeline(count: int) -> Mock:
    pipeline = Mock()
    pipeline.zremrangebyscore.return_value = pipeline
    pipeline.zadd.return_value = pipeline
    pipeline.zcard.return_value = pipeline
    pipeline.expire.return_value = pipeline
    pipeline.execute = AsyncMock(return_value=[0, 1, count, 1])
    return pipeline


def make_request(host: str):
    return SimpleNamespace(client=SimpleNamespace(host=host))


@pytest.mark.asyncio
async def test_under_limit() -> None:
    limiter = RateLimiter(TEST_RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS, TEST_RATE_LIMIT_PREFIX)
    redis = Mock()
    redis.pipeline.return_value = make_pipeline(count=5)

    await limiter(make_request("127.0.0.1"), redis)


@pytest.mark.asyncio
async def test_at_limit() -> None:
    limiter = RateLimiter(TEST_RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS, TEST_RATE_LIMIT_PREFIX)
    redis = Mock()
    redis.pipeline.return_value = make_pipeline(count=10)

    with pytest.raises(HTTPException) as exc_info:
        await limiter(make_request("127.0.0.1"), redis)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == str(RATE_LIMIT_WINDOW_SECONDS)


@pytest.mark.asyncio
async def test_over_limit() -> None:
    limiter = RateLimiter(TEST_RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS, TEST_RATE_LIMIT_PREFIX)
    redis = Mock()
    redis.pipeline.return_value = make_pipeline(count=15)

    with pytest.raises(HTTPException) as exc_info:
        await limiter(make_request("127.0.0.1"), redis)

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_different_ips_independent() -> None:
    limiter = RateLimiter(TEST_RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS, TEST_RATE_LIMIT_PREFIX)
    redis = Mock()
    first_pipeline = make_pipeline(count=5)
    second_pipeline = make_pipeline(count=5)
    redis.pipeline.side_effect = [first_pipeline, second_pipeline]

    await limiter(make_request("127.0.0.1"), redis)
    await limiter(make_request("10.0.0.2"), redis)

    assert first_pipeline.zremrangebyscore.call_args.args[0] == "rl:test:127.0.0.1"
    assert second_pipeline.zremrangebyscore.call_args.args[0] == "rl:test:10.0.0.2"
    assert first_pipeline.zadd.call_args.args[1] != second_pipeline.zadd.call_args.args[1]


@pytest.mark.asyncio
async def test_pipeline_called_atomically() -> None:
    limiter = RateLimiter(TEST_RATE_LIMIT, RATE_LIMIT_WINDOW_SECONDS, TEST_RATE_LIMIT_PREFIX)
    redis = Mock()
    redis.zremrangebyscore = Mock()
    redis.zadd = Mock()
    redis.zcard = Mock()
    redis.expire = Mock()
    pipeline = make_pipeline(count=5)
    redis.pipeline.return_value = pipeline

    await limiter(make_request("127.0.0.1"), redis)

    redis.pipeline.assert_called_once()
    pipeline.execute.assert_awaited_once()
    redis.zremrangebyscore.assert_not_called()
    redis.zadd.assert_not_called()
    redis.zcard.assert_not_called()
    redis.expire.assert_not_called()
