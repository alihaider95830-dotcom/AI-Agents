import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.deps import get_current_active_user, get_db
from backend.core.auth import get_current_user
from backend.db.models import ReportStatus, UserTier
from backend.api.v1.routes import reports as reports_route
from backend.main import app


class ScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class QueryResult:
    def __init__(self, *, scalar=None, scalars=None, row=None):
        self._scalar = scalar
        self._scalars = scalars
        self._row = row

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        return self._scalar

    def scalars(self):
        return ScalarResult(self._scalars or [])

    def one_or_none(self):
        return self._row


class FakeSession:
    def __init__(self):
        self.reports = {}
        self.jobs = {}
        self.users = {}
        self.usage_logs = []
        self._pending_users = {}
        self._pending_reports = {}
        self._pending_jobs = {}
        self._pending_usage_logs = []
        self._credit_snapshots = {}

    async def execute(self, statement):
        compiled = str(statement)

        if "count(" in compiled:
            active_reports = [report for report in self.reports.values() if report.deleted_at is None]
            return QueryResult(scalar=len(active_reports))

        if "JOIN reports" in compiled:
            for job in self.jobs.values():
                report = self.reports.get(job.report_id)
                if report and report.deleted_at is None:
                    return QueryResult(row=(job, report))
            return QueryResult(row=None)

        if "WHERE reports.id" in compiled:
            params = statement.compile().params
            report_id = params.get("id_1")
            user_id = params.get("user_id_1")
            report = self.reports.get(report_id)
            if report and report.user_id == user_id and report.deleted_at is None:
                return QueryResult(scalar=report)
            return QueryResult(scalar=None)

        if "FROM reports" in compiled:
            params = statement.compile().params
            user_id = params.get("user_id_1")
            reports = [
                report
                for report in self.reports.values()
                if report.user_id == user_id and report.deleted_at is None
            ]
            return QueryResult(scalars=reports)

        if "FROM users" in compiled:
            params = statement.compile().params
            user_id = params.get("id_1")
            user = self.users.get(user_id)
            if user is not None and user_id not in self._credit_snapshots:
                self._credit_snapshots[user_id] = user.credits_remaining
            return QueryResult(scalar=user)

        return QueryResult()

    def add(self, instance):
        if hasattr(instance, "action"):
            # UsageLog
            self._pending_usage_logs.append(instance)
        elif hasattr(instance, "email") and hasattr(instance, "credits_remaining"):
            self._pending_users[instance.id] = instance
        elif hasattr(instance, "report_id"):
            if instance.id is None:
                instance.id = uuid.uuid4()
            if getattr(instance, "created_at", None) is None:
                instance.created_at = datetime.now(timezone.utc)
            self._pending_jobs[instance.id] = instance
        else:
            if instance.id is None:
                instance.id = uuid.uuid4()
            if getattr(instance, "created_at", None) is None:
                instance.created_at = datetime.now(timezone.utc)
            self._pending_reports[instance.id] = instance

    async def flush(self):
        return None

    async def commit(self):
        self.users.update(self._pending_users)
        self.reports.update(self._pending_reports)
        self.jobs.update(self._pending_jobs)
        self.usage_logs.extend(self._pending_usage_logs)
        self._pending_users.clear()
        self._pending_reports.clear()
        self._pending_jobs.clear()
        self._pending_usage_logs.clear()
        self._credit_snapshots.clear()
        return None

    async def rollback(self):
        for user_id, credits_remaining in self._credit_snapshots.items():
            if user_id in self.users:
                self.users[user_id].credits_remaining = credits_remaining
        self._pending_users.clear()
        self._pending_reports.clear()
        self._pending_jobs.clear()
        self._pending_usage_logs.clear()
        self._credit_snapshots.clear()
        return None

    async def refresh(self, instance):
        return None


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


@pytest.fixture
def fake_db():
    return FakeSession()


@pytest_asyncio.fixture
async def client(fake_db, fake_user):
    async def override_get_db():
        yield fake_db

    async def override_get_current_user():
        return fake_user

    fake_db.users[fake_user.id] = fake_user

    celery_result = SimpleNamespace(id="celery-task-123")
    apply_async_mock = Mock(return_value=celery_result)
    reports_route.generate_report.apply_async = apply_async_mock

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_report_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/reports",
        json={
            "topic": "The future of AI report generation",
            "report_type": "market_analysis",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "report_id" in body
    assert "job_id" in body
    assert body["celery_task_id"] == "celery-task-123"
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_create_report_rolls_back_when_queue_publish_fails(
    client: AsyncClient,
    fake_db: FakeSession,
    fake_user,
) -> None:
    reports_route.generate_report.apply_async = Mock(side_effect=RuntimeError("broker unavailable"))

    response = await client.post(
        "/api/v1/reports",
        json={
            "topic": "A report request that cannot be queued",
            "report_type": "market_analysis",
        },
    )

    assert response.status_code == 500
    assert fake_user.credits_remaining == 2
    assert fake_db.reports == {}
    assert fake_db.jobs == {}
    assert fake_db.usage_logs == []


@pytest.mark.asyncio
async def test_create_report_invalid_type(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/reports",
        json={"topic": "A valid enough topic", "report_type": "unknown_type"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_report_topic_too_short(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/reports",
        json={"topic": "short", "report_type": "market_analysis"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_reports_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 10}


@pytest.mark.asyncio
async def test_get_report_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/reports/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_wrong_user(client: AsyncClient, fake_db, fake_other_user) -> None:
    report_id = uuid.uuid4()
    fake_db.reports[report_id] = SimpleNamespace(
        id=report_id,
        user_id=fake_other_user.id,
        title="Other report",
        topic="A report owned by someone else",
        report_type="market_analysis",
        status=ReportStatus.PENDING,
        content_md=None,
        word_count=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        deleted_at=None,
    )

    response = await client.get(f"/api/v1/reports/{report_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_report(client: AsyncClient, fake_db, fake_user) -> None:
    report_id = uuid.uuid4()
    fake_db.reports[report_id] = SimpleNamespace(
        id=report_id,
        user_id=fake_user.id,
        title="My report",
        topic="A report that will be deleted",
        report_type="market_analysis",
        status=ReportStatus.PENDING,
        content_md=None,
        word_count=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        deleted_at=None,
    )

    delete_response = await client.delete(f"/api/v1/reports/{report_id}")
    get_response = await client.get(f"/api/v1/reports/{report_id}")

    assert delete_response.status_code == 200
    assert get_response.status_code == 404
