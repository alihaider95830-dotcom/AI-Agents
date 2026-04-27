from __future__ import annotations

import html
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.core.exceptions import NotFoundError
from backend.core.logging import get_logger
from backend.db.models import Report, ReportStatus, User

try:
    import markdown as markdown_lib
except Exception:  # pragma: no cover - covered by dependency install in production
    markdown_lib = None  # type: ignore[assignment]

try:
    from weasyprint import HTML as WeasyHTML
except Exception:  # pragma: no cover - depends on platform PDF libraries
    WeasyHTML = None  # type: ignore[assignment]


router = APIRouter()
logger = get_logger(__name__)


def _format_report_type(report_type: str) -> str:
    return " ".join(part.capitalize() for part in report_type.split("_"))


def _format_completed_at(value: datetime | None) -> str:
    if value is None:
        return "Not available"
    return value.strftime("%B %d, %Y")


def _build_pdf_html(report: Report, html_body: str) -> str:
    report_type_label = html.escape(_format_report_type(report.report_type))
    generated_at = html.escape(_format_completed_at(report.completed_at))
    word_count = report.word_count or 0

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: Georgia, serif;
    font-size: 13px;
    line-height: 1.7;
    color: #1a1a1a;
    max-width: 720px;
    margin: 0 auto;
    padding: 40px 60px;
  }}
  h1 {{ font-size: 26px; font-weight: bold; margin-bottom: 8px; }}
  h2 {{ font-size: 20px; font-weight: bold; margin-top: 32px; }}
  h3 {{ font-size: 16px; font-weight: bold; margin-top: 24px; }}
  p  {{ margin: 12px 0; }}
  ul, ol {{ margin: 12px 0; padding-left: 24px; }}
  li {{ margin: 4px 0; }}
  blockquote {{
    border-left: 3px solid #ccc;
    margin: 16px 0;
    padding: 8px 16px;
    color: #555;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 12px;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 8px 12px;
    text-align: left;
  }}
  th {{ background: #f5f5f5; font-weight: bold; }}
  code {{
    background: #f5f5f5;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 12px;
  }}
  pre code {{
    display: block;
    padding: 12px;
    overflow-x: auto;
    background: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
  }}
  .report-meta {{
    color: #666;
    font-size: 12px;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid #eee;
  }}
  @page {{ margin: 2cm; }}
</style>
</head>
<body>
  <h1>{html.escape(report.topic)}</h1>
  <div class="report-meta">
    Report type: {report_type_label} &nbsp;|&nbsp;
    Generated: {generated_at} &nbsp;|&nbsp;
    {word_count} words
  </div>
  {html_body}
</body>
</html>"""


@router.get("/reports/{report_id}/export/pdf", response_model=None)
async def export_report_pdf(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")

    if report.status != ReportStatus.DONE:
        return JSONResponse(
            status_code=400,
            content={"error": "Report is not complete"},
        )

    if not report.content_md or not report.content_md.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Report has no content"},
        )

    try:
        if markdown_lib is None:
            raise RuntimeError("Markdown is not available")
        html_body = markdown_lib.markdown(
            report.content_md,
            extensions=["tables", "fenced_code", "nl2br"],
        )
        full_html = _build_pdf_html(report, html_body)
        if WeasyHTML is None:
            raise RuntimeError("WeasyPrint is not available")
        pdf_bytes = WeasyHTML(string=full_html).write_pdf()
    except Exception as exc:
        logger.exception("PDF generation failed for report_id=%s", report.id)
        return JSONResponse(
            status_code=500,
            content={
                "error": "PDF generation failed. Please try downloading as markdown."
            },
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="studio-report-{str(report.id)[:8]}.pdf"'
            )
        },
    )
