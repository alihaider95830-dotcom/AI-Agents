from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.schemas.jobs import JobResponse
from backend.core.exceptions import NotFoundError
from backend.db.models import Job, Report, User

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobResponse:
    result = await db.execute(
        select(Job, Report)
        .join(Report, Job.report_id == Report.id)
        .where(
            Job.id == job_id,
            Report.user_id == current_user.id,
            Report.deleted_at.is_(None),
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Job not found")

    job, report = row
    return JobResponse(
        job_id=job.id,
        report_id=report.id,
        status=report.status.value,
        current_agent=job.current_agent,
        progress_pct=job.progress_pct,
        error_message=job.error_message,
        created_at=job.created_at,
    )
