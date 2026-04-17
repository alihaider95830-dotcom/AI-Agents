from __future__ import annotations

import logging
import time

from agents.planner import run_planner
from agents.researcher import run_researcher
from agents.writer import run_writer
from exceptions import PipelineError
from schemas.findings import FindingsOutput
from schemas.draft import ReportDraft
from schemas.outline import ReportOutline

logger = logging.getLogger(__name__)


def run_research_and_plan(topic: str) -> tuple[FindingsOutput, ReportOutline]:
    """Run the researcher and planner steps and return both validated outputs."""
    current_step = "researcher"
    try:
        research_started_at = time.perf_counter()
        findings = run_researcher(topic)
        research_elapsed = time.perf_counter() - research_started_at
        logger.info("Researcher completed for topic=%s in %.2fs", topic, research_elapsed)

        current_step = "planner"
        planning_started_at = time.perf_counter()
        outline = run_planner(findings)
        planning_elapsed = time.perf_counter() - planning_started_at
        logger.info("Planner completed for topic=%s in %.2fs", topic, planning_elapsed)

        return findings, outline
    except Exception as exc:
        logger.exception("Pipeline failed during %s for topic=%s", current_step, topic)
        raise PipelineError(
            f"Pipeline failed during {current_step} step for topic '{topic}': {exc}"
        ) from exc


def run_full_pipeline(topic: str) -> tuple[FindingsOutput, ReportOutline, ReportDraft]:
    """Run the researcher, planner, and writer steps and return all validated outputs."""
    pipeline_started_at = time.perf_counter()
    current_step = "researcher"

    try:
        research_started_at = time.perf_counter()
        findings = run_researcher(topic)
        research_elapsed = time.perf_counter() - research_started_at
        logger.info("Researcher completed for topic=%s in %.2fs", topic, research_elapsed)

        current_step = "planner"
        planning_started_at = time.perf_counter()
        outline = run_planner(findings)
        planning_elapsed = time.perf_counter() - planning_started_at
        logger.info("Planner completed for topic=%s in %.2fs", topic, planning_elapsed)

        current_step = "writer"
        writing_started_at = time.perf_counter()
        draft = run_writer(outline, findings)
        writing_elapsed = time.perf_counter() - writing_started_at
        logger.info("Writer completed for topic=%s in %.2fs", topic, writing_elapsed)

        total_elapsed = time.perf_counter() - pipeline_started_at
        logger.info("Full pipeline completed for topic=%s in %.2fs", topic, total_elapsed)

        return findings, outline, draft
    except Exception as exc:
        logger.exception("Full pipeline failed during %s for topic=%s", current_step, topic)
        raise PipelineError(
            f"Pipeline failed during {current_step} step for topic '{topic}': {exc}"
        ) from exc
