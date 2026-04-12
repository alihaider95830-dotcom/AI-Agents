from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.models import User, UserTier
from backend.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@lru_cache
def _get_jwk_client() -> PyJWKClient:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL is not configured",
        )
    return PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


async def _verify_legacy_supabase_token(token: str) -> dict[str, Any]:
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase URL is not configured",
        )

    api_key = settings.supabase_service_key or settings.supabase_anon_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase API key is not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers={
                    "apikey": api_key,
                    "Authorization": f"Bearer {token}",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_data = response.json()
    unverified_payload = jwt.decode(
        token,
        options={"verify_signature": False, "verify_exp": False, "verify_aud": False},
    )
    unverified_payload["sub"] = user_data.get("id")
    unverified_payload["email"] = user_data.get("email")
    return unverified_payload


async def verify_supabase_jwt(token: str) -> dict[str, Any]:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg", "")

        if algorithm.startswith("HS"):
            payload = await _verify_legacy_supabase_token(token)
        else:
            signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[algorithm] if algorithm else None,
                options={"verify_aud": False},
            )
    except HTTPException:
        raise
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if "sub" not in payload or "email" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = await verify_supabase_jwt(token)
    supabase_id = payload["sub"]
    email = payload["email"]

    try:
        uuid.UUID(supabase_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    result = await db.execute(select(User).where(User.supabase_id == supabase_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            supabase_id=supabase_id,
            tier=UserTier.FREE,
            credits_remaining=2,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user

