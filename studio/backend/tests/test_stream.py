import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.routes import stream as stream_route
from backend.core.auth import get_current_user
from backend.db.models import UserTier
from backend.main import app


class StreamQueryResult:
    def __init__(self, scalar):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeStreamDb:
    def __init__(self, allowed_job_id):
        self.allowed_job_id = allowed_job_id

    async def execute(self, statement):
        params = statement.compile().params
        job_id = params.get("id_1")
        if job_id == self.allowed_job_id:
            return StreamQueryResult(job_id)
        return StreamQueryResult(None)


class FakePubSub:
    def __init__(self, messages):
        self.messages = list(messages)
        self.unsubscribed = False
        self.closed = False

    async def subscribe(self, channel):
        return None

    async def get_message(self, ignore_subscribe_messages=True, timeout=30):
        if self.messages:
            return {"data": json.dumps(self.messages.pop(0))}
        return None

    async def unsubscribe(self, channel):
        self.unsubscribed = True

    async def close(self):
        self.closed = True


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="user@example.com",
        tier=UserTier.FREE,
        credits_remaining=2,
    )


@pytest_asyncio.fixture
async def client(fake_user, monkeypatch):
    job_id = uuid.uuid4()
    fake_db = FakeStreamDb(job_id)

    async def override_get_db():
        yield fake_db

    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client, job_id

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_stream_receives_events(client, monkeypatch) -> None:
    async_client, job_id = client
    monkeypatch.setattr(
        stream_route,
        "_create_pubsub",
        lambda: FakePubSub([{"type": "progress", "pct": 10}, {"type": "done", "pct": 100}]),
    )

    async with async_client.stream("GET", f"/api/v1/stream/{job_id}") as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    assert response.status_code == 200
    assert "event: progress" in body
    assert 'data: {"type": "progress", "pct": 10}' in body


@pytest.mark.asyncio
async def test_stream_closes_on_done(client, monkeypatch) -> None:
    async_client, job_id = client
    pubsub = FakePubSub([{"type": "done", "pct": 100}])
    monkeypatch.setattr(stream_route, "_create_pubsub", lambda: pubsub)

    async with async_client.stream("GET", f"/api/v1/stream/{job_id}") as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    assert response.status_code == 200
    assert "event: done" in body
    assert 'data: {"type": "done", "pct": 100}' in body
    assert pubsub.unsubscribed is True
    assert pubsub.closed is True


@pytest.mark.asyncio
async def test_stream_wrong_user(client, monkeypatch) -> None:
    async_client, _ = client
    monkeypatch.setattr(stream_route, "_create_pubsub", lambda: FakePubSub([]))

    response = await async_client.get(f"/api/v1/stream/{uuid.uuid4()}")

    assert response.status_code == 403

