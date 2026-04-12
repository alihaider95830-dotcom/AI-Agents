from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.api.v1.schemas.reports import (
    ReportCreate,
    ReportCreateResponse,
    ReportDetail,
    ReportListItem,
    ReportListResponse,
)
from backend.core.exceptions import InsufficientCreditsError, NotFoundError
from backend.db.models import Job, Report, ReportStatus, UsageLog, User
from backend.workers.tasks import generate_report

router = APIRouter()


def _serialize_report_list_item(report: Report) -> ReportListItem:
    return ReportListItem(
        id=report.id,
        title=report.title,
        topic=report.topic,
        report_type=report.report_type,
        status=report.status.value,
        created_at=report.created_at,
        completed_at=report.completed_at,
    )


def _serialize_report_detail(report: Report) -> ReportDetail:
    return ReportDetail(
        id=report.id,
        title=report.title,
        topic=report.topic,
        report_type=report.report_type,
        status=report.status.value,
        content_md=report.content_md,
        word_count=report.word_count,
        created_at=report.created_at,
        completed_at=report.completed_at,
    )


async def _get_user_report(
    db: AsyncSession,
    report_id: UUID,
    user_id: UUID,
) -> Report | None:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user_id,
            Report.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


@router.post("/reports", response_model=ReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReportCreateResponse:
    locked_user_result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    locked_user = locked_user_result.scalar_one()

    if locked_user.credits_remaining <= 0:
        raise InsufficientCreditsError()

    report = Report(
        user_id=locked_user.id,
        title=payload.topic[:255],
        topic=payload.topic,
        report_type=payload.report_type,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.flush()

    job = Job(report_id=report.id)
    db.add(job)
    await db.flush()

    locked_user.credits_remaining -= 1
    usage_log = UsageLog(
        user_id=locked_user.id,
        report_id=report.id,
        action="generate_report",
        delta=-1,
    )
    db.add(usage_log)

    try:
        celery_result = generate_report.apply_async(
            args=[str(report.id), str(locked_user.id)],
            countdown=1,
        )
        job.celery_task_id = celery_result.id
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    current_user.credits_remaining = locked_user.credits_remaining
    await db.refresh(report)
    await db.refresh(job)

    return ReportCreateResponse(
        report_id=report.id,
        job_id=job.id,
        celery_task_id=job.celery_task_id or "",
        status=ReportStatus.PENDING.value,
    )


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReportListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 50)
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Report)
        .where(
            Report.user_id == current_user.id,
            Report.deleted_at.is_(None),
        )
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    count_result = await db.execute(
        select(func.count())
        .select_from(Report)
        .where(
            Report.user_id == current_user.id,
            Report.deleted_at.is_(None),
        )
    )

    reports = result.scalars().all()
    total = count_result.scalar_one()

    return ReportListResponse(
        items=[_serialize_report_list_item(report) for report in reports],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReportDetail:
    report = await _get_user_report(db, report_id, current_user.id)
    if report is None:
        raise NotFoundError("Report not found")

    return _serialize_report_detail(report)


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    report = await _get_user_report(db, report_id, current_user.id)
    if report is None:
        raise NotFoundError("Report not found")

    report.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "deleted"}
