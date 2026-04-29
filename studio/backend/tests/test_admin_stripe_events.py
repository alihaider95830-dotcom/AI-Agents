from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_db
from backend.api.v1.routes import admin as admin_route
from backend.main import app


class ScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class QueryResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return ScalarResult(self._items)


class FakeAdminDb:
    def __init__(self, events):
        self.events = events

    async def execute(self, statement):
        return QueryResult(self.events)


class FakeSyncSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


def make_event(**overrides):
    data = {
        "id": "evt_123",
        "type": "invoice.payment_failed",
        "status": "failed",
        "processed_at": None,
        "error_message": "boom",
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_list_stripe_events_requires_admin_key(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/stripe-events")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_stripe_events_returns_rows(client: AsyncClient) -> None:
    event = make_event()

    async def override_get_db():
        yield FakeAdminDb([event])

    app.dependency_overrides[get_db] = override_get_db

    response = await client.get(
        "/api/v1/admin/stripe-events",
        headers={"X-Admin-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.json()[0]["id"] == "evt_123"
    assert response.json()[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_replay_stripe_event_uses_processor(
    client: AsyncClient,
    monkeypatch,
) -> None:
    class FakeProcessor:
        def __init__(self, db):
            self.db = db

        def process(self, event):
            assert event["id"] == "evt_123"
            return "processed"

    monkeypatch.setattr(
        admin_route.stripe_client,
        "retrieve_event",
        lambda event_id: {"id": event_id, "type": "invoice.payment_failed"},
    )
    monkeypatch.setattr(admin_route, "SyncSessionLocal", lambda: FakeSyncSession())
    monkeypatch.setattr(admin_route, "WebhookProcessor", FakeProcessor)

    response = await client.post(
        "/api/v1/admin/stripe-events/evt_123/replay",
        headers={"X-Admin-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"replayed": True, "result": "processed"}
