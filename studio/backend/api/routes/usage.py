from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

from backend.core.auth import get_current_user
from backend.db.models import User, UsageLog, Report
from backend.db.session import get_db

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = 30,
) -> dict:
    """Get user usage statistics."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get total reports created
    report_result = await db.execute(
        select(func.count(Report.id)).where(
            Report.user_id == current_user.id,
            Report.created_at >= since,
        )
    )
    reports_created = report_result.scalar() or 0
    
    # Get credits used
    usage_result = await db.execute(
        select(func.sum(UsageLog.delta)).where(
            UsageLog.user_id == current_user.id,
            UsageLog.created_at >= since,
        )
    )
    credits_used = abs(usage_result.scalar() or 0)
    
    # Get total reports ever
    total_reports_result = await db.execute(
        select(func.count(Report.id)).where(Report.user_id == current_user.id)
    )
    total_reports = total_reports_result.scalar() or 0
    
    return {
        "user_id": str(current_user.id),
        "tier": current_user.tier.value,
        "credits_remaining": current_user.credits_remaining,
        "period_days": days,
        "reports_created_in_period": reports_created,
        "credits_used_in_period": credits_used,
        "total_reports_ever": total_reports,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/logs")
async def get_usage_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """Get detailed usage logs."""
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == current_user.id)
        .order_by(UsageLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "action": log.action,
                "delta": log.delta,
                "report_id": str(log.report_id) if log.report_id else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "skip": skip,
        "limit": limit,
        "total_count": len(logs),
    }


@router.get("/monthly")
async def get_monthly_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    months: int = 12,
) -> dict:
    """Get monthly usage breakdown."""
    from sqlalchemy import extract
    
    result = await db.execute(
        select(
            extract("year", Report.created_at).label("year"),
            extract("month", Report.created_at).label("month"),
            func.count(Report.id).label("reports"),
        )
        .where(
            Report.user_id == current_user.id,
            Report.created_at >= datetime.now(timezone.utc) - timedelta(days=30*months),
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )
    
    monthly_data = result.all()
    
    return {
        "monthly_breakdown": [
            {
                "year": int(row.year),
                "month": int(row.month),
                "reports_created": row.reports,
            }
            for row in monthly_data
        ]
    }
