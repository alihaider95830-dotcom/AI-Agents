from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.schemas.jobs import JobCancelResponse, JobResponse
from backend.core.exceptions import NotFoundError
from backend.db.models import Job, Report, ReportStatus, User
from backend.workers.celery_app import celery_app

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


@router.delete("/jobs/{job_id}", response_model=JobCancelResponse)
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobCancelResponse:
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

    cancellable_statuses = {ReportStatus.PENDING, ReportStatus.RUNNING}
    if report.status not in cancellable_statuses:
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be cancelled: current status is '{report.status.value}'.",
        )

    report.status = ReportStatus.CANCELLED
    job.error_message = "Cancelled by user"

    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    await db.commit()
    return JobCancelResponse(status="cancelled")
