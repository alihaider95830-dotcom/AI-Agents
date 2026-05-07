from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.auth import get_current_user
from backend.db.models import User, UserSettings, APIKey
from backend.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get user profile details."""
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other user's profile")
    
    settings = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = settings.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "tier": current_user.tier.value,
        "credits_remaining": current_user.credits_remaining,
        "stripe_customer_id": current_user.stripe_customer_id,
        "settings": {
            "notifications_enabled": user_settings.notifications_enabled if user_settings else True,
            "email_on_report_complete": user_settings.email_on_report_complete if user_settings else True,
            "theme": user_settings.theme if user_settings else "light",
            "default_export_format": user_settings.default_export_format if user_settings else "markdown",
        } if user_settings else None,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat(),
    }


@router.put("/{user_id}")
async def update_user_profile(
    user_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update user profile."""
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot update other user's profile")
    
    # Update allowed fields only
    allowed_fields = {"email"}  # Add more as needed
    for field in allowed_fields:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    
    await db.commit()
    await db.refresh(current_user)
    
    return {"message": "Profile updated", "user_id": str(current_user.id)}


@router.get("/{user_id}/api-keys")
async def list_api_keys(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List API keys for the user."""
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other user's API keys")
    
    result = await db.execute(select(APIKey).where(APIKey.user_id == current_user.id))
    api_keys = result.scalars().all()
    
    return [
        {
            "id": str(key.id),
            "name": key.name,
            "created_at": key.created_at.isoformat(),
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        }
        for key in api_keys
    ]


@router.post("/{user_id}/settings")
async def update_user_settings(
    user_id: str,
    settings_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update user settings."""
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot update other user's settings")
    
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    user_settings = result.scalar_one_or_none()
    
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.add(user_settings)
    
    # Update allowed settings
    allowed_settings = {"notifications_enabled", "email_on_report_complete", "theme", "default_export_format"}
    for setting in allowed_settings:
        if setting in settings_data:
            setattr(user_settings, setting, settings_data[setting])
    
    await db.commit()
    
    return {"message": "Settings updated"}
