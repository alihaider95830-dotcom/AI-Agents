import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.routes import export as export_route
from backend.core.auth import get_current_user
from backend.db.models import ReportStatus, UserTier
from backend.main import app


class QueryResult:
    def __init__(self, scalar=None):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeExportDb:
    def __init__(self, report=None):
        self.report = report

    async def execute(self, statement):
        params = statement.compile().params
        report_id = params.get("id_1")
        user_id = params.get("user_id_1")

        if (
            self.report is not None
            and self.report.id == report_id
            and self.report.user_id == user_id
            and self.report.deleted_at is None
        ):
            return QueryResult(self.report)

        return QueryResult(None)


class FakeWeasyHTML:
    def __init__(self, string):
        self.string = string

    def write_pdf(self):
        return b"%PDF-1.4 test"


class BrokenWeasyHTML:
    def __init__(self, string):
        self.string = string

    def write_pdf(self):
        raise RuntimeError("pdf engine unavailable")


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="user@example.com",
        tier=UserTier.FREE,
        credits_remaining=2,
    )


@pytest.fixture
def fake_other_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="other@example.com",
        tier=UserTier.FREE,
        credits_remaining=2,
    )


@pytest.fixture(autouse=True)
def fake_markdown(monkeypatch):
    monkeypatch.setattr(
        export_route,
        "markdown_lib",
        SimpleNamespace(markdown=lambda value, extensions: "<h1>Report</h1>"),
    )


def make_report(user_id, status=ReportStatus.DONE, content_md="# Report\nBody"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Exportable report",
        topic="Exportable report topic",
        report_type="market_analysis",
        status=status,
        content_md=content_md,
        word_count=250,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        deleted_at=None,
    )


@pytest_asyncio.fixture
async def client(fake_user):
    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


def override_db(report):
    async def _override_get_db():
        yield FakeExportDb(report)

    app.dependency_overrides[get_db] = _override_get_db


@pytest.mark.asyncio
async def test_export_pdf_success(client: AsyncClient, fake_user, monkeypatch) -> None:
    report = make_report(fake_user.id)
    override_db(report)
    monkeypatch.setattr(export_route, "WeasyHTML", FakeWeasyHTML)

    response = await client.get(f"/api/v1/reports/{report.id}/export/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "studio-report-" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_export_pdf_not_done(client: AsyncClient, fake_user, monkeypatch) -> None:
    report = make_report(fake_user.id, status=ReportStatus.RUNNING)
    override_db(report)
    monkeypatch.setattr(export_route, "WeasyHTML", FakeWeasyHTML)

    response = await client.get(f"/api/v1/reports/{report.id}/export/pdf")

    assert response.status_code == 400
    assert response.json()["error"] == "Report is not complete"


@pytest.mark.asyncio
async def test_export_pdf_no_content(client: AsyncClient, fake_user, monkeypatch) -> None:
    report = make_report(fake_user.id, content_md=None)
    override_db(report)
    monkeypatch.setattr(export_route, "WeasyHTML", FakeWeasyHTML)

    response = await client.get(f"/api/v1/reports/{report.id}/export/pdf")

    assert response.status_code == 400
    assert response.json()["error"] == "Report has no content"


@pytest.mark.asyncio
async def test_export_pdf_wrong_user(
    client: AsyncClient,
    fake_other_user,
    monkeypatch,
) -> None:
    report = make_report(fake_other_user.id)
    override_db(report)
    monkeypatch.setattr(export_route, "WeasyHTML", FakeWeasyHTML)

    response = await client.get(f"/api/v1/reports/{report.id}/export/pdf")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_pdf_weasyprint_error(
    client: AsyncClient,
    fake_user,
    monkeypatch,
) -> None:
    report = make_report(fake_user.id)
    override_db(report)
    monkeypatch.setattr(export_route, "WeasyHTML", BrokenWeasyHTML)

    response = await client.get(f"/api/v1/reports/{report.id}/export/pdf")

    assert response.status_code == 500
    assert response.json()["error"] == (
        "PDF generation failed. Please try downloading as markdown."
    )
