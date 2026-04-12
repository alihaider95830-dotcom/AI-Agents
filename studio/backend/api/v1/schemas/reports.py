from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AllowedReportType = Literal[
    "market_analysis",
    "competitor_overview",
    "trend_report",
    "industry_deep_dive",
]


class ReportCreate(BaseModel):
    topic: str = Field(min_length=10, max_length=500)
    report_type: AllowedReportType


class ReportCreateResponse(BaseModel):
    report_id: UUID
    job_id: UUID
    celery_task_id: str
    status: str


class ReportListItem(BaseModel):
    id: UUID
    title: str
    topic: str
    report_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class ReportDetail(ReportListItem):
    content_md: str | None = None
    word_count: int | None = None


class ReportListResponse(BaseModel):
    items: list[ReportListItem]
    total: int
    page: int
    page_size: int
