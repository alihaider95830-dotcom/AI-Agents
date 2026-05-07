from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from backend.core.auth import get_current_user
from backend.db.models import User, Report, Job, ReportStatus
from backend.db.session import get_db
from backend.workers.celery_app import celery_app

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get report details."""
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access report you don't own")
    
    # Get job info
    job_result = await db.execute(
        select(Job).where(Job.report_id == report.id)
    )
    job = job_result.scalar_one_or_none()
    
    return {
        "id": str(report.id),
        "title": report.title,
        "topic": report.topic,
        "report_type": report.report_type,
        "status": report.status.value,
        "content_md": report.content_md,
        "word_count": report.word_count,
        "job": {
            "id": str(job.id) if job else None,
            "current_agent": job.current_agent if job else None,
            "progress_pct": job.progress_pct if job else 0,
            "error_message": job.error_message if job else None,
        },
        "created_at": report.created_at.isoformat(),
        "completed_at": report.completed_at.isoformat() if report.completed_at else None,
        "updated_at": report.updated_at.isoformat(),
    }


@router.post("/{report_id}/regenerate")
async def regenerate_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Regenerate/restart a report pipeline."""
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot regenerate report you don't own")
    
    # Check if already running
    if report.status == ReportStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Report is already being generated")
    
    # Reset report and job
    report.status = ReportStatus.PENDING
    report.content_md = None
    report.word_count = None
    
    job_result = await db.execute(
        select(Job).where(Job.report_id == report.id)
    )
    job = job_result.scalar_one_or_none()
    
    if job:
        job.celery_task_id = None
        job.current_agent = None
        job.progress_pct = 0
        job.error_message = None
    
    await db.commit()
    
    # Queue generation task
    celery_app.send_task(
        "backend.workers.tasks.generate_report",
        args=[str(report.id), str(current_user.id)],
    )
    
    return {
        "message": "Report regeneration started",
        "report_id": str(report.id),
        "status": ReportStatus.PENDING.value,
    }


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft delete a report."""
    from datetime import datetime, timezone
    
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete report you don't own")
    
    report.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Report deleted"}


@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """List user's reports with optional filtering."""
    query = select(Report).where(Report.user_id == current_user.id)
    
    if status:
        try:
            status_enum = ReportStatus(status)
            query = query.where(Report.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Exclude soft-deleted reports
    query = query.where(Report.deleted_at.is_(None))
    
    # Order by creation date, newest first
    from sqlalchemy import desc
    query = query.order_by(desc(Report.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return {
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "topic": r.topic,
                "report_type": r.report_type,
                "status": r.status.value,
                "word_count": r.word_count,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in reports
        ]
    }
