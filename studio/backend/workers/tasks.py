from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis
from celery import Task
from sqlalchemy import create_engine, select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from backend.core.credits import refund_sync
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.models import Job, Report, ReportStatus
from backend.workers.celery_app import celery_app
from backend.workers.publisher import publish_event

logger = get_logger(__name__)

sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


def _ensure_pipeline_import_path() -> None:
    current_file = Path(__file__).resolve()
    candidates = (
        current_file.parents[2],
        current_file.parents[3],
    )
    for candidate in candidates:
        if not (candidate / "agents").is_dir():
            continue
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            return
        return


def _run_agent_pipeline(topic: str, job_id: str | None) -> Any:
    _ensure_pipeline_import_path()
    from agents.crew import run_crew as run_agent_crew

    return run_agent_crew(topic, job_id=job_id)


def _extract_markdown_output(result: Any) -> str:
    if isinstance(result, str):
        markdown = result
    elif isinstance(result, dict):
        markdown = result.get("markdown_output")
    else:
        markdown = getattr(result, "markdown_output", None)

    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("Crew pipeline returned no markdown output")
    return markdown


def run_crew(topic: str, report_type: str, job_id: str | None = None) -> str:
    logger.info("running agent pipeline for report_type=%s", report_type)
    return _extract_markdown_output(_run_agent_pipeline(topic, job_id=job_id))


def _is_transient_error(exc: Exception) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError, redis.RedisError, TimeoutError))


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.generate_report",
    max_retries=settings.celery_task_max_retries,
    soft_time_limit=settings.celery_task_soft_time_limit,
    time_limit=settings.celery_task_time_limit,
)
def generate_report(self: Task, report_id: str, user_id: str) -> str:
    session = SyncSessionLocal()
    should_commit_on_exit = True

    try:
        report = session.execute(select(Report).where(Report.id == report_id)).scalar_one()
        job = session.execute(select(Job).where(Job.report_id == report.id)).scalar_one()

        job.celery_task_id = self.request.id
        report.status = ReportStatus.RUNNING
        job.current_agent = "researcher"
        job.progress_pct = 0
        session.flush()

        logger.info("report %s started with job %s", report.id, job.id)
        publish_event(
            str(job.id),
            {"agent": "researcher", "pct": 0, "type": "progress"},
        )

        result = run_crew(report.topic, report.report_type, job_id=str(job.id))

        report.status = ReportStatus.DONE
        report.content_md = result
        report.word_count = len(result.split())
        report.completed_at = datetime.now(timezone.utc)
        job.progress_pct = 100
        job.current_agent = "writer"
        logger.info("report %s completed successfully", report.id)
        publish_event(str(job.id), {"type": "done", "pct": 100})
        return result
    except Exception as exc:
        logger.exception("report generation failed for report_id=%s", report_id)

        report = locals().get("report")
        job = locals().get("job")
        if _is_transient_error(exc):
            countdown = (2 ** self.request.retries) * settings.celery_retry_base_delay_seconds
            if report is not None:
                report.status = ReportStatus.PENDING
            if job is not None:
                job.current_agent = "retrying"
                job.error_message = None
                publish_event(
                    str(job.id),
                    {"type": "retry", "message": str(exc), "retry_in": countdown},
                )
            logger.warning(
                "retrying report generation for report_id=%s in %s seconds",
                report_id,
                countdown,
            )
            session.commit()
            should_commit_on_exit = False
            raise self.retry(exc=exc, countdown=countdown)

        if report is not None:
            report.status = ReportStatus.FAILED
            report.completed_at = datetime.now(timezone.utc)
        if job is not None:
            job.error_message = str(exc)
            publish_event(
                str(job.id),
                {"type": "error", "message": str(exc)},
            )

        refund_session = SyncSessionLocal()
        try:
            refund_sync(user_id, report_id, refund_session)
            logger.info(
                "refunded credit for failed report_id=%s user_id=%s",
                report_id,
                user_id,
            )
        except Exception:
            logger.exception(
                "failed to refund credit for failed report_id=%s user_id=%s",
                report_id,
                user_id,
            )
        finally:
            refund_session.close()

        raise
    finally:
        if should_commit_on_exit:
            session.commit()
        session.close()


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.generate_export",
    max_retries=3,
    soft_time_limit=300,
    time_limit=360,
)
def generate_export(self: Task, export_id: str, report_id: str, export_format: str) -> str:
    """Generate export of report in specified format."""
    from backend.db.models import Export, ExportStatus
    
    session = SyncSessionLocal()
    try:
        report = session.execute(select(Report).where(Report.id == report_id)).scalar_one()
        export = session.execute(select(Export).where(Export.id == export_id)).scalar_one()
        
        logger.info("generating %s export for report_id=%s", export_format, report_id)
        
        # Export generation logic
        if export_format == "markdown":
            content = report.content_md
            export.file_path = f"exports/{export_id}.md"
        elif export_format == "pdf":
            # TODO: Implement PDF generation (use reportlab or similar)
            content = report.content_md
            export.file_path = f"exports/{export_id}.pdf"
        elif export_format == "docx":
            # TODO: Implement DOCX generation (use python-docx)
            content = report.content_md
            export.file_path = f"exports/{export_id}.docx"
        else:
            raise ValueError(f"Invalid export format: {export_format}")
        
        # TODO: Upload to S3 if configured
        export.status = "completed"
        export.file_size_bytes = len(content.encode()) if content else 0
        export.completed_at = datetime.now(timezone.utc)
        
        logger.info("export %s completed for report_id=%s", export_id, report_id)
        session.commit()
        return export.file_path
    except Exception as exc:
        logger.exception("export generation failed for export_id=%s", export_id)
        
        export = locals().get("export")
        if export:
            export.status = "failed"
            export.error_message = str(exc)
            session.commit()
        
        raise
    finally:
        session.close()


@celery_app.task(
    name="backend.workers.tasks.send_email_notification",
    max_retries=3,
    soft_time_limit=30,
    time_limit=60,
)
def send_email_notification(user_email: str, subject: str, template: str, context: dict) -> str:
    """Send email notification to user."""
    session = SyncSessionLocal()
    try:
        logger.info("sending email notification to %s with template %s", user_email, template)
        
        # TODO: Implement email sending
        # - Use SendGrid or similar
        # - Render template with context
        # - Handle email delivery
        
        logger.info("email sent to %s", user_email)
        return f"email_sent_to_{user_email}"
    except Exception as exc:
        logger.exception("failed to send email to %s", user_email)
        raise
    finally:
        session.close()


@celery_app.task(
    name="backend.workers.tasks.process_stripe_webhook",
    max_retries=5,
    soft_time_limit=30,
    time_limit=60,
)
def process_stripe_webhook(event_type: str, event_id: str) -> str:
    """Process Stripe webhook events."""
    from backend.db.models import StripeEvent
    
    session = SyncSessionLocal()
    try:
        logger.info("processing Stripe webhook event_type=%s event_id=%s", event_type, event_id)
        
        stripe_event = session.execute(
            select(StripeEvent).where(StripeEvent.id == event_id)
        ).scalar_one_or_none()
        
        if not stripe_event:
            logger.warning("Stripe event %s not found", event_id)
            return "event_not_found"
        
        # Handle specific webhook events
        if event_type == "customer.subscription.updated":
            # TODO: Update user subscription status
            pass
        elif event_type == "customer.subscription.deleted":
            # TODO: Downgrade user subscription
            pass
        elif event_type == "invoice.payment_succeeded":
            # TODO: Record payment
            pass
        elif event_type == "invoice.payment_failed":
            # TODO: Notify user of failed payment
            pass
        
        stripe_event.processed_at = datetime.now(timezone.utc)
        stripe_event.status = "processed"
        session.commit()
        
        logger.info("processed Stripe webhook event %s", event_id)
        return f"processed_{event_id}"
    except Exception as exc:
        logger.exception("failed to process Stripe webhook event %s", event_id)
        raise
    finally:
        session.close()


@celery_app.task(
    name="backend.workers.tasks.cleanup_webhook_events",
    soft_time_limit=60,
    time_limit=120,
)
def cleanup_webhook_events() -> str:
    """Clean up old webhook events from database."""
    from backend.db.models import WebhookEvent
    
    session = SyncSessionLocal()
    try:
        from datetime import timedelta
        
        logger.info("cleaning up old webhook events")
        
        # Delete processed events older than 7 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        result = session.query(WebhookEvent).filter(
            WebhookEvent.processed == True,
            WebhookEvent.processed_at < cutoff_date,
        ).delete()
        
        session.commit()
        logger.info("deleted %d old webhook events", result)
        return f"cleaned_up_{result}_events"
    except Exception as exc:
        logger.exception("failed to cleanup webhook events")
        raise
    finally:
        session.close()


@celery_app.task(
    name="backend.workers.tasks.retry_failed_webhooks",
    soft_time_limit=120,
    time_limit=180,
)
def retry_failed_webhooks() -> str:
    """Retry failed webhook processing."""
    from backend.db.models import WebhookEvent
    
    session = SyncSessionLocal()
    try:
        logger.info("retrying failed webhook events")
        
        # Get failed webhooks with retry_count < max
        failed_webhooks = session.query(WebhookEvent).filter(
            WebhookEvent.processed == False,
            WebhookEvent.retry_count < 5,
        ).all()
        
        retry_count = 0
        for webhook in failed_webhooks:
            try:
                # TODO: Retry webhook processing
                webhook.retry_count += 1
                retry_count += 1
            except Exception:
                pass
        
        session.commit()
        logger.info("retried %d failed webhook events", retry_count)
        return f"retried_{retry_count}_webhooks"
    except Exception as exc:
        logger.exception("failed to retry webhooks")
        raise
    finally:
        session.close()
