import os
from unittest.mock import AsyncMock, Mock

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/studio")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("VECTOR_STORE_PATH", "./data/faiss_index")


@pytest.fixture
def fake_redis():
    pipeline = Mock()
    pipeline.zremrangebyscore.return_value = pipeline
    pipeline.zadd.return_value = pipeline
    pipeline.zcard.return_value = pipeline
    pipeline.expire.return_value = pipeline
    pipeline.execute = AsyncMock(return_value=[0, 1, 1, 1])

    redis = Mock()
    redis.pipeline.return_value = pipeline
    return redis


@pytest.fixture(autouse=True)
def override_redis_dependency(fake_redis):
    from backend.api.deps import get_redis
    from backend.main import app

    async def _override_get_redis():
        return fake_redis

    app.dependency_overrides[get_redis] = _override_get_redis
    yield
    app.dependency_overrides.pop(get_redis, None)
