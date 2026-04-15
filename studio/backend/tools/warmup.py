from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.db.models import Report, ReportStatus
from backend.tools.store_manager import store_manager

logger = get_logger(__name__)


async def warm_vector_stores(db: AsyncSession) -> None:
    result = await db.execute(
        select(Report.id).where(
            Report.status == ReportStatus.RUNNING,
            Report.deleted_at.is_(None),
        )
    )
    report_ids = result.scalars().all()

    warmed_count = 0
    for report_id in report_ids:
        try:
            store_manager.get(str(report_id), auto_load=True)
            warmed_count += 1
        except Exception as exc:
            logger.warning("failed to warm vector store %s: %s", report_id, exc)

    logger.info("Warmed %s vector stores", warmed_count)
