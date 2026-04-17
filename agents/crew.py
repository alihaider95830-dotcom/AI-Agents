from __future__ import annotations

import logging
import time

from agents.planner import run_planner
from agents.qa import run_qa
from agents.researcher import run_researcher
from agents.writer import run_writer
from exceptions import PipelineError
from schemas.report import FinalReport

logger = logging.getLogger(__name__)
PIPELINE_VERSION = "1.0.0"


def run_crew(topic: str, job_id: str | None = None) -> FinalReport:
    """Run the full 4-agent pipeline and return the final QA-approved report."""
    overall_started_at = time.perf_counter()
    current_step = "Researcher"
    logger.info("Starting full crew pipeline for topic=%s", topic)

    try:
        step_started_at = time.perf_counter()
        findings = run_researcher(topic)
        logger.info(
            "%s step completed for topic=%s in %.2fs",
            current_step,
            topic,
            time.perf_counter() - step_started_at,
        )

        current_step = "Planner"
        step_started_at = time.perf_counter()
        outline = run_planner(findings)
        logger.info(
            "%s step completed for topic=%s in %.2fs",
            current_step,
            topic,
            time.perf_counter() - step_started_at,
        )

        current_step = "Writer"
        step_started_at = time.perf_counter()
        draft = run_writer(outline, findings)
        logger.info(
            "%s step completed for topic=%s in %.2fs",
            current_step,
            topic,
            time.perf_counter() - step_started_at,
        )

        current_step = "QA"
        step_started_at = time.perf_counter()
        report = run_qa(draft, findings)
        logger.info(
            "%s step completed for topic=%s in %.2fs",
            current_step,
            topic,
            time.perf_counter() - step_started_at,
        )

        if job_id is not None:
            report = report.model_copy(update={"job_id": job_id})

        logger.info(
            "Full crew pipeline completed for topic=%s in %.2fs",
            topic,
            time.perf_counter() - overall_started_at,
        )
        return report
    except Exception as exc:
        logger.exception(
            "Full crew pipeline failed during %s for topic=%s",
            current_step,
            topic,
        )
        raise PipelineError(
            f"{current_step} step failed for topic '{topic}': {exc}"
        ) from exc


def get_crew_status() -> dict[str, str]:
    """Return a simple readiness payload for the FastAPI health endpoint."""
    return {
        "researcher": "ready",
        "planner": "ready",
        "writer": "ready",
        "qa": "ready",
        "pipeline_version": PIPELINE_VERSION,
    }
