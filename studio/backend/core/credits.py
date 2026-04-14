from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.core.exceptions import InsufficientCreditsError, StudioException
from backend.db.models import Report, ReportStatus, UsageLog, User

TIER_LIMITS = {
    "free": {"monthly_reports": 2, "max_word_count": 500},
    "pro": {"monthly_reports": 20, "max_word_count": 10000},
    "agency": {"monthly_reports": None, "max_word_count": None},
}

CREDIT_DEDUCTED_ACTION = "credit_deducted"
CREDIT_REFUNDED_ACTION = "credit_refunded"
CREDITS_DB_ERROR_MESSAGE = "Failed to update credits"


def _tier_value(user: User) -> str:
    tier = getattr(user, "tier", "free")
    return tier.value if hasattr(tier, "value") else str(tier)


def _first_day_of_current_month(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _first_day_of_next_month(now: datetime) -> datetime:
    if now.month == 12:
        return now.replace(
            year=now.year + 1,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    return now.replace(
        month=now.month + 1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _coerce_uuid(value: str | None) -> uuid.UUID | None:
    if value is None:
        return None

    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


async def _count_reports_this_month(user: User, db: AsyncSession) -> int:
    month_start = _first_day_of_current_month(datetime.now(timezone.utc))
    result = await db.execute(
        select(func.count())
        .select_from(Report)
        .where(
            Report.user_id == user.id,
            Report.created_at >= month_start,
            Report.status != ReportStatus.FAILED,
        )
    )
    return result.scalar_one()


async def check_and_deduct(user: User, db: AsyncSession) -> None:
    try:
        locked_user_result = await db.execute(
            select(User).where(User.id == user.id).with_for_update()
        )
        locked_user = locked_user_result.scalar_one()

        tier = _tier_value(locked_user)
        limit = TIER_LIMITS[tier]["monthly_reports"]
        reports_this_month = await _count_reports_this_month(locked_user, db)

        if limit is not None and reports_this_month >= limit:
            raise InsufficientCreditsError(
                f"Monthly limit of {limit} reports reached. Upgrade to generate more."
            )

        locked_user.credits_remaining = max(locked_user.credits_remaining - 1, 0)
        user.credits_remaining = locked_user.credits_remaining
        db.add(locked_user)
        db.add(
            UsageLog(
                user_id=locked_user.id,
                report_id=None,
                action=CREDIT_DEDUCTED_ACTION,
                delta=-1,
            )
        )
        await db.flush()
    except InsufficientCreditsError:
        raise
    except SQLAlchemyError as exc:
        await db.rollback()
        raise StudioException(CREDITS_DB_ERROR_MESSAGE, 500) from exc


async def refund(
    user: User,
    db: AsyncSession,
    report_id: str | None,
) -> None:
    try:
        user.credits_remaining += 1
        db.add(user)
        db.add(
            UsageLog(
                user_id=user.id,
                report_id=_coerce_uuid(report_id),
                action=CREDIT_REFUNDED_ACTION,
                delta=1,
            )
        )
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise StudioException(CREDITS_DB_ERROR_MESSAGE, 500) from exc


def refund_sync(user_id: str, report_id: str, session: Session) -> None:
    lookup_user_id = _coerce_uuid(user_id) or user_id
    user = session.get(User, lookup_user_id)
    if user is None:
        return

    try:
        user.credits_remaining += 1
        session.add(user)
        session.add(
            UsageLog(
                user_id=user.id,
                report_id=_coerce_uuid(report_id),
                action=CREDIT_REFUNDED_ACTION,
                delta=1,
            )
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


async def get_usage_summary(user: User, db: AsyncSession) -> dict[str, int | str | None]:
    now = datetime.now(timezone.utc)
    try:
        reports_this_month = await _count_reports_this_month(user, db)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise StudioException(CREDITS_DB_ERROR_MESSAGE, 500) from exc

    tier = _tier_value(user)
    return {
        "tier": tier,
        "credits_remaining": user.credits_remaining,
        "reports_this_month": reports_this_month,
        "monthly_limit": TIER_LIMITS[tier]["monthly_reports"],
        "resets_on": _first_day_of_next_month(now).strftime("%Y-%m-%d"),
    }
