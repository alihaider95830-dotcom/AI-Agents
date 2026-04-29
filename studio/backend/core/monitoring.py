from __future__ import annotations

from ipaddress import ip_address

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.models import Report, ReportStatus, User, UserTier
from backend.db.session import get_db


def _client_ip_is_allowed(request: Request) -> bool:
    if request.client is None:
        return False

    client_host = request.client.host
    if client_host in settings.metrics_allowed_ips:
        return True

    try:
        parsed_ip = ip_address(client_host)
    except ValueError:
        return False

    return parsed_ip.is_loopback or parsed_ip.is_private


def _token_is_allowed(token: str | None) -> bool:
    return bool(settings.metrics_token) and token == settings.metrics_token


async def metrics_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_metrics_token: str | None = Header(default=None),
) -> PlainTextResponse:
    if not _token_is_allowed(x_metrics_token) and not _client_ip_is_allowed(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    report_counts: dict[str, int] = {}
    report_result = await db.execute(
        select(Report.status, func.count()).group_by(Report.status)
    )
    for status, count in report_result.all():
        key = status.value if hasattr(status, "value") else str(status)
        report_counts[key] = int(count)

    user_counts: dict[str, int] = {}
    user_result = await db.execute(select(User.tier, func.count()).group_by(User.tier))
    for tier, count in user_result.all():
        key = tier.value if hasattr(tier, "value") else str(tier)
        user_counts[key] = int(count)

    active_jobs = report_counts.get(ReportStatus.RUNNING.value, 0)
    lines = [
        "# HELP studio_reports_total Total reports generated",
        "# TYPE studio_reports_total counter",
    ]
    for status in (
        ReportStatus.DONE.value,
        ReportStatus.FAILED.value,
        ReportStatus.RUNNING.value,
    ):
        lines.append(
            f'studio_reports_total{{status="{status}"}} {report_counts.get(status, 0)}'
        )

    lines.extend(
        [
            "# HELP studio_active_jobs Currently running jobs",
            "# TYPE studio_active_jobs gauge",
            f"studio_active_jobs {active_jobs}",
            "# HELP studio_users_total Total registered users by tier",
            "# TYPE studio_users_total gauge",
        ]
    )

    for tier in (UserTier.FREE.value, UserTier.PRO.value, UserTier.AGENCY.value):
        lines.append(f'studio_users_total{{tier="{tier}"}} {user_counts.get(tier, 0)}')

    return PlainTextResponse("\n".join(lines) + "\n")


def register_metrics_route(app: FastAPI) -> None:
    app.add_api_route(
        "/metrics",
        metrics_endpoint,
        methods=["GET"],
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
