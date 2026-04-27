from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_current_active_user
from backend.core import stripe_client
from backend.db.models import UserTier
from backend.main import app


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="user@example.com",
        tier=UserTier.PRO,
        credits_remaining=20,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
        subscription_status="past_due",
    )


@pytest_asyncio.fixture
async def client(fake_user):
    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_current_active_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retry_payment_success(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(
        stripe_client,
        "list_open_invoices",
        Mock(return_value=SimpleNamespace(data=[SimpleNamespace(id="in_123")])),
    )
    pay_mock = Mock()
    monkeypatch.setattr(stripe_client, "pay_invoice", pay_mock)

    response = await client.post("/api/v1/billing/retry-payment")

    assert response.status_code == 200
    assert response.json() == {"retry_initiated": True, "invoice_id": "in_123"}
    pay_mock.assert_called_once_with("in_123")


@pytest.mark.asyncio
async def test_retry_payment_no_subscription(
    client: AsyncClient,
    fake_user,
) -> None:
    fake_user.stripe_subscription_id = None

    response = await client.post("/api/v1/billing/retry-payment")

    assert response.status_code == 400
    assert response.json()["error"] == "No active subscription"


@pytest.mark.asyncio
async def test_retry_payment_not_past_due(
    client: AsyncClient,
    fake_user,
) -> None:
    fake_user.subscription_status = "active"

    response = await client.post("/api/v1/billing/retry-payment")

    assert response.status_code == 400
    assert response.json()["error"] == "No payment retry needed"


@pytest.mark.asyncio
async def test_retry_payment_no_open_invoice(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(
        stripe_client,
        "list_open_invoices",
        Mock(return_value=SimpleNamespace(data=[])),
    )

    response = await client.post("/api/v1/billing/retry-payment")

    assert response.status_code == 400
    assert response.json()["error"] == "No open invoice found"


@pytest.mark.asyncio
async def test_retry_payment_card_declined(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr(
        stripe_client,
        "list_open_invoices",
        Mock(return_value=SimpleNamespace(data=[SimpleNamespace(id="in_123")])),
    )
    monkeypatch.setattr(
        stripe_client,
        "pay_invoice",
        Mock(side_effect=stripe_client.StripeCardError("declined", "Insufficient funds")),
    )

    response = await client.post("/api/v1/billing/retry-payment")

    assert response.status_code == 402
    assert response.json()["error"] == "Payment method declined"
    assert response.json()["detail"] == "Insufficient funds"
