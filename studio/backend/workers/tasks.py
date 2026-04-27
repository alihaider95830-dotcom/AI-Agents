from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis
from celery import Task
from sqlalchemy import create_engine, select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from backend.core.credits import refund_sync
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.models import Job, Report, ReportStatus
from backend.workers.celery_app import celery_app
from backend.workers.publisher import publish_event

logger = get_logger(__name__)

sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


def _ensure_pipeline_import_path() -> None:
    current_file = Path(__file__).resolve()
    candidates = (
        current_file.parents[2],
        current_file.parents[3],
    )
    for candidate in candidates:
        if not (candidate / "agents").is_dir():
            continue
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            return
        return


def _run_agent_pipeline(topic: str, job_id: str | None) -> Any:
    _ensure_pipeline_import_path()
    from agents.crew import run_crew as run_agent_crew

    return run_agent_crew(topic, job_id=job_id)


def _extract_markdown_output(result: Any) -> str:
    if isinstance(result, str):
        markdown = result
    elif isinstance(result, dict):
        markdown = result.get("markdown_output")
    else:
        markdown = getattr(result, "markdown_output", None)

    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("Crew pipeline returned no markdown output")
    return markdown


def run_crew(topic: str, report_type: str, job_id: str | None = None) -> str:
    logger.info("running agent pipeline for report_type=%s", report_type)
    return _extract_markdown_output(_run_agent_pipeline(topic, job_id=job_id))


def _is_transient_error(exc: Exception) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError, redis.RedisError, TimeoutError))


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.generate_report",
    max_retries=settings.celery_task_max_retries,
    soft_time_limit=settings.celery_task_soft_time_limit,
    time_limit=settings.celery_task_time_limit,
)
def generate_report(self: Task, report_id: str, user_id: str) -> str:
    session = SyncSessionLocal()
    should_commit_on_exit = True

    try:
        report = session.execute(select(Report).where(Report.id == report_id)).scalar_one()
        job = session.execute(select(Job).where(Job.report_id == report.id)).scalar_one()

        job.celery_task_id = self.request.id
        report.status = ReportStatus.RUNNING
        job.current_agent = "researcher"
        job.progress_pct = 0
        session.flush()

        logger.info("report %s started with job %s", report.id, job.id)
        publish_event(
            str(job.id),
            {"agent": "researcher", "pct": 0, "type": "progress"},
        )

        result = run_crew(report.topic, report.report_type, job_id=str(job.id))

        report.status = ReportStatus.DONE
        report.content_md = result
        report.word_count = len(result.split())
        report.completed_at = datetime.now(timezone.utc)
        job.progress_pct = 100
        job.current_agent = "writer"
        logger.info("report %s completed successfully", report.id)
        publish_event(str(job.id), {"type": "done", "pct": 100})
        return result
    except Exception as exc:
        logger.exception("report generation failed for report_id=%s", report_id)

        report = locals().get("report")
        job = locals().get("job")
        if _is_transient_error(exc):
            countdown = (2 ** self.request.retries) * settings.celery_retry_base_delay_seconds
            if report is not None:
                report.status = ReportStatus.PENDING
            if job is not None:
                job.current_agent = "retrying"
                job.error_message = None
                publish_event(
                    str(job.id),
                    {"type": "retry", "message": str(exc), "retry_in": countdown},
                )
            logger.warning(
                "retrying report generation for report_id=%s in %s seconds",
                report_id,
                countdown,
            )
            session.commit()
            should_commit_on_exit = False
            raise self.retry(exc=exc, countdown=countdown)

        if report is not None:
            report.status = ReportStatus.FAILED
            report.completed_at = datetime.now(timezone.utc)
        if job is not None:
            job.error_message = str(exc)
            publish_event(
                str(job.id),
                {"type": "error", "message": str(exc)},
            )

        refund_session = SyncSessionLocal()
        try:
            refund_sync(user_id, report_id, refund_session)
            logger.info(
                "refunded credit for failed report_id=%s user_id=%s",
                report_id,
                user_id,
            )
        except Exception:
            logger.exception(
                "failed to refund credit for failed report_id=%s user_id=%s",
                report_id,
                user_id,
            )
        finally:
            refund_session.close()

        raise
    finally:
        if should_commit_on_exit:
            session.commit()
        session.close()
