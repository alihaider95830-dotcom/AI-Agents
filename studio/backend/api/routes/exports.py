from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from backend.core.auth import get_current_user
from backend.db.models import User, Report, Export, ReportStatus
from backend.db.session import get_db
from backend.workers.celery_app import celery_app

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/reports/{report_id}/export")
async def create_export(
    report_id: str,
    export_format: str,  # pdf, docx, markdown
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create an export of a report."""
    if export_format not in ["pdf", "docx", "markdown"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # Verify report ownership and completion
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot export report you don't own")
    
    if report.status != ReportStatus.DONE:
        raise HTTPException(status_code=400, detail="Report must be completed before export")
    
    # Create export record
    export = Export(
        report_id=report.id,
        user_id=current_user.id,
        export_format=export_format,
        status="pending",
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    
    # Queue export task
    celery_app.send_task(
        "backend.workers.tasks.generate_export",
        args=[str(export.id), str(report.id), export_format],
    )
    
    return {
        "export_id": str(export.id),
        "status": "pending",
        "format": export_format,
        "created_at": export.created_at.isoformat(),
    }


@router.get("/reports/{report_id}")
async def list_report_exports(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all exports for a report."""
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access report exports you don't own")
    
    export_result = await db.execute(
        select(Export).where(Export.report_id == report.id)
    )
    exports = export_result.scalars().all()
    
    return [
        {
            "id": str(export.id),
            "format": export.export_format,
            "status": export.status,
            "file_size_bytes": export.file_size_bytes,
            "created_at": export.created_at.isoformat(),
            "completed_at": export.completed_at.isoformat() if export.completed_at else None,
        }
        for export in exports
    ]


@router.get("/{export_id}")
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get export status and download link."""
    result = await db.execute(
        select(Export).where(Export.id == uuid.UUID(export_id))
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    
    if export.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access export you don't own")
    
    return {
        "id": str(export.id),
        "format": export.export_format,
        "status": export.status,
        "file_path": export.file_path if export.status == "completed" else None,
        "file_size_bytes": export.file_size_bytes,
        "error_message": export.error_message if export.status == "failed" else None,
        "created_at": export.created_at.isoformat(),
        "completed_at": export.completed_at.isoformat() if export.completed_at else None,
    }
