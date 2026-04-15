from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.routes.admin import verify_admin_key
from backend.core.exceptions import NotFoundError
from backend.db.models import Report, User
from backend.tools.store_manager import store_manager

router = APIRouter(prefix="/knowledge")


async def _get_user_report(
    report_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Report:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


@router.get("/{report_id}/status")
async def get_knowledge_status(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    report = await _get_user_report(report_id, current_user, db)
    store = store_manager.get(str(report.id))
    return store.health_check()


@router.get("/{report_id}/sources")
async def get_knowledge_sources(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    report = await _get_user_report(report_id, current_user, db)
    store = store_manager.get(str(report.id))
    sources = store.list_sources()
    return {"sources": sources, "count": len(sources)}


@router.delete("/{report_id}")
async def delete_knowledge_index(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, object]:
    report = await _get_user_report(report_id, current_user, db)
    index_name = str(report.id)
    store = store_manager.get(index_name, auto_load=False)
    store.clear()
    store_manager.release(index_name)
    return {"deleted": True, "index_name": index_name}


@router.get(
    "/admin/health",
    dependencies=[Depends(verify_admin_key)],
)
async def get_knowledge_admin_health(
    _: User = Depends(get_current_active_user),
) -> dict[str, dict]:
    return store_manager.health_report()


@router.get(
    "/admin/active",
    dependencies=[Depends(verify_admin_key)],
)
async def get_knowledge_admin_active(
    _: User = Depends(get_current_active_user),
) -> dict[str, list[str]]:
    return {"active_indexes": store_manager.list_active()}
