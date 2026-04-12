from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.core.config import settings
from backend.core.exceptions import ForbiddenError
from backend.core.logging import get_logger
from backend.db.models import Job, Report, User

logger = get_logger(__name__)
router = APIRouter()


def _create_pubsub() -> aioredis.client.PubSub:
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return client.pubsub()


async def _job_belongs_to_user(
    db: AsyncSession,
    job_id: UUID,
    user_id: UUID,
) -> bool:
    result = await db.execute(
        select(Job.id)
        .join(Report, Job.report_id == Report.id)
        .where(
            Job.id == job_id,
            Report.user_id == user_id,
            Report.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def _event_stream(request: Request, job_id: str) -> AsyncIterator[str]:
    pubsub = _create_pubsub()
    channel = f"job:{job_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            if await request.is_disconnected():
                break

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=settings.stream_keepalive_timeout_seconds,
            )

            if message is None:
                yield ": keepalive\n\n"
                continue

            data = message.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8")

            payload = json.loads(data)
            event_type = payload.get("type", "message")
            yield f"event: {event_type}\ndata: {data}\n\n"

            if event_type in {"done", "error"}:
                break
    finally:
        logger.info("closing stream subscription for job %s", job_id)
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.get("/stream/{job_id}", response_model=None)
async def stream_job(
    job_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    if not await _job_belongs_to_user(db, job_id, current_user.id):
        raise ForbiddenError("You do not have access to this job")

    return StreamingResponse(
        _event_stream(request, str(job_id)),
        media_type="text/event-stream",
    )
