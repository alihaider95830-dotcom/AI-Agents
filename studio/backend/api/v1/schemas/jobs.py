from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobResponse(BaseModel):
    job_id: UUID
    report_id: UUID
    status: str
    current_agent: str | None = None
    progress_pct: int
    error_message: str | None = None
    created_at: datetime
