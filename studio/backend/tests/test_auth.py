from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.db.session import get_db
from backend.main import app


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest_asyncio.fixture
async def client(mock_db_session: AsyncMock):
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client: AsyncClient, mock_db_session: AsyncMock) -> None:
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer garbage-token"},
    )

    assert response.status_code == 401
    mock_db_session.execute.assert_not_awaited()
