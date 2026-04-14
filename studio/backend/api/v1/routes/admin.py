from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.core.config import settings
from backend.core.credits import TIER_LIMITS, get_usage_summary
from backend.core.exceptions import NotFoundError
from backend.db.models import UsageLog, User, UserTier

AGENCY_ADMIN_CREDIT_BALANCE = 9999
ADMIN_KEY_ERROR_DETAIL = "Invalid admin key"
VALID_TIERS = tuple(TIER_LIMITS.keys())


async def verify_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail=ADMIN_KEY_ERROR_DETAIL)


router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(verify_admin_key)],
)


class AdjustCreditsRequest(BaseModel):
    delta: int
    reason: str


class SetTierRequest(BaseModel):
    tier: str


async def _get_user_by_id(user_id: UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    return user


@router.post("/users/{user_id}/adjust-credits")
async def adjust_user_credits(
    user_id: UUID,
    payload: AdjustCreditsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str | None]:
    user = await _get_user_by_id(user_id, db)
    user.credits_remaining = max(0, user.credits_remaining + payload.delta)
    db.add(user)
    db.add(
        UsageLog(
            user_id=user.id,
            report_id=None,
            action="admin_adjustment",
            delta=payload.delta,
        )
    )
    await db.commit()
    await db.refresh(user)
    return await get_usage_summary(user, db)


@router.post("/users/{user_id}/set-tier")
async def set_user_tier(
    user_id: UUID,
    payload: SetTierRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str | None]:
    if payload.tier not in VALID_TIERS:
        raise HTTPException(status_code=422, detail="Invalid tier")

    user = await _get_user_by_id(user_id, db)
    user.tier = UserTier(payload.tier)
    if payload.tier == UserTier.AGENCY.value:
        user.credits_remaining = AGENCY_ADMIN_CREDIT_BALANCE
    else:
        monthly_limit = TIER_LIMITS[payload.tier]["monthly_reports"]
        user.credits_remaining = monthly_limit or 0

    db.add(user)
    db.add(
        UsageLog(
            user_id=user.id,
            report_id=None,
            action="tier_change",
            delta=0,
        )
    )
    await db.commit()
    await db.refresh(user)
    return await get_usage_summary(user, db)
