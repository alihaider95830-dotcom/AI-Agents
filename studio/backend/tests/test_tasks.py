from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.db.models import ReportStatus
from backend.workers import tasks


class FakeSyncSession:
    def __init__(self, report, job):
        self.report = report
        self.job = job
        self.commit_calls = 0
        self.closed = False

    def execute(self, statement):
        compiled = str(statement)
        if "FROM reports" in compiled:
            return SimpleNamespace(scalar_one=lambda: self.report)
        if "FROM jobs" in compiled:
            return SimpleNamespace(scalar_one=lambda: self.job)
        raise AssertionError(f"Unexpected statement: {compiled}")

    def flush(self):
        return None

    def commit(self):
        self.commit_calls += 1

    def close(self):
        self.closed = True


@pytest.fixture
def fake_entities():
    report = SimpleNamespace(
        id="report-1",
        topic="A valid report topic",
        report_type="market_analysis",
        status=ReportStatus.PENDING,
        content_md=None,
        completed_at=None,
    )
    job = SimpleNamespace(
        id="job-1",
        report_id="report-1",
        celery_task_id=None,
        current_agent=None,
        progress_pct=0,
        error_message=None,
    )
    return report, job


def test_generate_report_success(monkeypatch, fake_entities):
    report, job = fake_entities
    session = FakeSyncSession(report, job)
    monkeypatch.setattr(tasks, "SyncSessionLocal", lambda: session)
    publisher = Mock()
    monkeypatch.setattr(tasks, "publish_event", publisher)
    monkeypatch.setattr(tasks, "run_crew", lambda topic, report_type: "PLACEHOLDER REPORT CONTENT")
    retry = Mock(side_effect=AssertionError("retry should not be called"))
    monkeypatch.setattr(tasks.generate_report, "request", SimpleNamespace(id="celery-1", retries=0), raising=False)
    monkeypatch.setattr(tasks.generate_report, "retry", retry, raising=False)

    result = tasks.generate_report.run("report-1", "user-1")

    assert result == "PLACEHOLDER REPORT CONTENT"
    assert report.status == ReportStatus.DONE
    assert job.progress_pct == 100
    assert publisher.call_args_list[-1].args[1]["type"] == "done"


def test_generate_report_failure(monkeypatch, fake_entities):
    report, job = fake_entities
    session = FakeSyncSession(report, job)
    monkeypatch.setattr(tasks, "SyncSessionLocal", lambda: session)
    publisher = Mock()
    monkeypatch.setattr(tasks, "publish_event", publisher)

    def raise_error(topic, report_type):
        raise ValueError("boom")

    monkeypatch.setattr(tasks, "run_crew", raise_error)
    retry = Mock(side_effect=AssertionError("retry should not be called"))
    monkeypatch.setattr(tasks.generate_report, "request", SimpleNamespace(id="celery-2", retries=0), raising=False)
    monkeypatch.setattr(tasks.generate_report, "retry", retry, raising=False)

    with pytest.raises(ValueError):
        tasks.generate_report.run("report-1", "user-1")

    assert report.status == ReportStatus.FAILED
    assert job.error_message == "boom"
    assert publisher.call_args_list[-1].args[1]["type"] == "error"


def test_generate_report_retries(monkeypatch, fake_entities):
    report, job = fake_entities
    session = FakeSyncSession(report, job)
    monkeypatch.setattr(tasks, "SyncSessionLocal", lambda: session)
    publisher = Mock()
    monkeypatch.setattr(tasks, "publish_event", publisher)

    def raise_timeout(topic, report_type):
        raise TimeoutError("temporary issue")

    monkeypatch.setattr(tasks, "run_crew", raise_timeout)
    retry = Mock(side_effect=RuntimeError("retry requested"))
    monkeypatch.setattr(tasks.generate_report, "request", SimpleNamespace(id="celery-3", retries=2), raising=False)
    monkeypatch.setattr(tasks.generate_report, "retry", retry, raising=False)

    with pytest.raises(RuntimeError, match="retry requested"):
        tasks.generate_report.run("report-1", "user-1")

    retry.assert_called_once()
    assert retry.call_args.kwargs["countdown"] == 20
    assert report.status == ReportStatus.PENDING
    assert job.error_message is None
    assert publisher.call_args_list[-1].args[1]["type"] == "retry"
