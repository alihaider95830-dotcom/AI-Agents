from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_user
from backend.db.models import User
from backend.db.session import get_db

router = APIRouter(tags=["auth"])


def _serialize_user(user: User) -> dict[str, str | int]:
    return {
        "id": str(user.id),
        "email": user.email,
        "tier": user.tier.value,
        "credits_remaining": user.credits_remaining,
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> dict[str, str | int]:
    return _serialize_user(current_user)


@router.post("/me/sync")
async def sync_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    await db.refresh(current_user)
    return _serialize_user(current_user)
