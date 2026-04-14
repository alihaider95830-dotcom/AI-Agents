from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.core.credits import get_usage_summary
from backend.db.models import UsageLog, User

router = APIRouter(prefix="/billing")


@router.get("/usage")
async def get_billing_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, int | str | None]:
    return await get_usage_summary(current_user, db)


@router.get("/history")
async def get_billing_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict[str, object]]:
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == current_user.id)
        .order_by(UsageLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()

    return [
        {
            "action": log.action,
            "delta": log.delta,
            "report_id": str(log.report_id) if log.report_id else None,
            "created_at": log.created_at,
        }
        for log in logs
    ]
