from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.models import Report, ReportStatus
from backend.workers.celery_app import celery_app

CLEANUP_VECTOR_STORES_TASK_NAME = "cleanup_vector_stores"
CLEANUP_RETENTION_DAYS = 7
CLEANUP_SUMMARY_MESSAGE = "Vector store cleanup complete | scanned=%s deleted=%s errors=%s"

logger = get_logger(__name__)
sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


def _report_retention_reference(report: Report) -> datetime | None:
    if report.status == ReportStatus.FAILED:
        return report.completed_at or report.updated_at
    return report.completed_at


def _should_delete_report_index(report: Report | None, cutoff: datetime) -> bool:
    if report is None:
        return True
    if report.status not in {ReportStatus.DONE, ReportStatus.FAILED}:
        return False
    retention_reference = _report_retention_reference(report)
    if retention_reference is None:
        return False
    return retention_reference < cutoff


@celery_app.task(name=CLEANUP_VECTOR_STORES_TASK_NAME)
def cleanup_old_indexes() -> dict[str, int]:
    base_path = Path(settings.vector_store_path)
    summary = {"scanned": 0, "deleted": 0, "errors": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(days=CLEANUP_RETENTION_DAYS)
    session = SyncSessionLocal()

    try:
        if not base_path.exists():
            logger.info(
                CLEANUP_SUMMARY_MESSAGE,
                summary["scanned"],
                summary["deleted"],
                summary["errors"],
            )
            return summary

        for index_path in base_path.iterdir():
            if not index_path.is_dir():
                continue

            summary["scanned"] += 1
            try:
                try:
                    report_id = uuid.UUID(index_path.name)
                except ValueError:
                    report = None
                else:
                    report = session.get(Report, report_id)

                if _should_delete_report_index(report, cutoff):
                    shutil.rmtree(index_path)
                    summary["deleted"] += 1
            except Exception:
                summary["errors"] += 1
    finally:
        session.close()

    logger.info(
        CLEANUP_SUMMARY_MESSAGE,
        summary["scanned"],
        summary["deleted"],
        summary["errors"],
    )
    return summary
