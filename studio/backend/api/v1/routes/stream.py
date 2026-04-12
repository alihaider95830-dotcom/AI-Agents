from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db
from backend.core.auth import verify_supabase_jwt, get_current_user
from backend.core.config import settings
from backend.core.event_store import async_get_events
from backend.core.logging import get_logger
from backend.core.redis_client import get_async_redis
from backend.db.models import Job, Report, ReportStatus, User

logger = get_logger(__name__)
router = APIRouter()


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


async def _get_report_status(db: AsyncSession, job_id: UUID) -> ReportStatus | None:
    result = await db.execute(
        select(Report.status)
        .join(Job, Job.report_id == Report.id)
        .where(Job.id == job_id)
    )
    return result.scalar_one_or_none()


async def _event_stream(
    request: Request,
    job_id: str,
    last_event_id: int,
    db: AsyncSession,
) -> AsyncIterator[str]:
    logger.info("starting stream for job_id=%s, last_event_id=%d", job_id, last_event_id)

    # 1. Replay missed events
    missed_events = await async_get_events(job_id, from_index=last_event_id)
    
    current_index = last_event_id
    for payload in missed_events:
        event_type = payload.get("type", "message")
        yield f"id: {current_index}\nevent: {event_type}\ndata: {json.dumps(payload)}\n\n"
        current_index += 1
        if event_type in {"done", "error"}:
            return

    # 2. Check if job already finished to avoid subscribing unnecessarily
    job_uuid = UUID(job_id)
    status = await _get_report_status(db, job_uuid)
    if status in {ReportStatus.DONE, ReportStatus.FAILED}:
        return

    # 3. Subscribe to pubsub
    client = get_async_redis()
    pubsub = client.pubsub()
    channel = f"job:{job_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            if await request.is_disconnected():
                break

            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=settings.stream_keepalive_timeout_seconds,
                )
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue

            if message is None:
                continue

            data = message.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8")

            payload = json.loads(data)
            event_type = payload.get("type", "message")
            
            yield f"id: {current_index}\nevent: {event_type}\ndata: {data}\n\n"
            current_index += 1

            if event_type in {"done", "error"}:
                break
    finally:
        logger.info("closing stream subscription for job_id=%s", job_id)
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.get("/stream/{job_id}")
async def stream_job(
    request: Request,
    job_id: UUID,
    last_event_id: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "Missing or invalid authorization", "code": 401},
        )
    
    token = auth_header.split(" ")[1]
    try:
        # We process the auth here exactly how get_current_user does
        # but inside the endpoint to avoid dependency issues with StreamingResponse mid-stream failures
        current_user = await get_current_user(token=token, db=db)
    except Exception as exc:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token", "code": 401},
        )

    if not await _job_belongs_to_user(db, job_id, current_user.id):
        return JSONResponse(
            status_code=403,
            content={"error": "You do not have access to this job", "code": 403},
        )

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    
    return StreamingResponse(
        _event_stream(request, str(job_id), last_event_id, db),
        media_type="text/event-stream",
        headers=headers,
    )
