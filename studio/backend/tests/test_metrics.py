from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_db
from backend.db.models import ReportStatus, UserTier
from backend.main import app


class QueryResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeMetricsDb:
    def __init__(self):
        self.execute_count = 0

    async def execute(self, statement):
        self.execute_count += 1
        if self.execute_count == 1:
            return QueryResult(
                [
                    (ReportStatus.DONE, 3),
                    (ReportStatus.FAILED, 1),
                    (ReportStatus.RUNNING, 2),
                ]
            )
        return QueryResult(
            [
                (UserTier.FREE, 5),
                (UserTier.PRO, 2),
                (UserTier.AGENCY, 1),
            ]
        )


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        yield FakeMetricsDb()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_metrics_returns_prometheus_text(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert 'studio_reports_total{status="done"} 3' in response.text
    assert "studio_active_jobs 2" in response.text
    assert 'studio_users_total{tier="agency"} 1' in response.text
    assert response.headers["x-request-id"]
