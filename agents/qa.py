from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import appdirs
except ImportError:  # pragma: no cover - depends on environment
    appdirs = None

from agents.writer import assemble_markdown
from exceptions import QAError
from schemas.draft import ReportDraft, SectionDraft, count_words
from schemas.findings import FindingsOutput
from schemas.report import FinalReport, QAFlag

logger = logging.getLogger(__name__)
CREWAI_LOCALAPPDATA_ENV_VAR = "QA_CREWAI_LOCALAPPDATA"
REAL_CREW_ENV_VAR = "QA_USE_REAL_CREWAI"
DEFAULT_QA_MODEL = "gpt-4o-mini"
DEFAULT_MIN_QUALITY_SCORE = 0.75
DEFAULT_MAX_FLAGS_ALLOWED = 10
DEFAULT_AUTO_FIX_GRAMMAR = True
DEFAULT_AUTO_FIX_CLARITY = True
SECTION_SNIPPET_LENGTH = 200

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDIO_ROOT = REPO_ROOT / "studio"
if STUDIO_ROOT.exists() and str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

CREWAI_STORAGE_ROOT = REPO_ROOT / ".crewai"
CREWAI_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
CREWAI_LOCALAPPDATA_ROOT = CREWAI_STORAGE_ROOT / "localappdata"
CREWAI_LOCALAPPDATA_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["LOCALAPPDATA"] = os.getenv(
    CREWAI_LOCALAPPDATA_ENV_VAR,
    str(CREWAI_LOCALAPPDATA_ROOT),
)
os.environ.setdefault("CREWAI_STORAGE_DIR", "workspace")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
if appdirs is not None:
    appdirs.user_data_dir = lambda app_name, app_author=None: str(
        CREWAI_STORAGE_ROOT / (app_author or "CrewAI") / app_name
    )


@dataclass(slots=True)
class QAConfig:
    """Runtime configuration for the QA agent."""

    model_name: str = field(
        default_factory=lambda: os.getenv("QA_MODEL_NAME", DEFAULT_QA_MODEL)
    )
    min_quality_score: float = field(
        default_factory=lambda: float(
            os.getenv("QA_MIN_QUALITY_SCORE", DEFAULT_MIN_QUALITY_SCORE)
        )
    )
    max_flags_allowed: int = field(
        default_factory=lambda: int(
            os.getenv("QA_MAX_FLAGS_ALLOWED", DEFAULT_MAX_FLAGS_ALLOWED)
        )
    )
    auto_fix_grammar: bool = field(
        default_factory=lambda: _parse_bool_env(
            "QA_AUTO_FIX_GRAMMAR",
            DEFAULT_AUTO_FIX_GRAMMAR,
        )
    )
    auto_fix_clarity: bool = field(
        default_factory=lambda: _parse_bool_env(
            "QA_AUTO_FIX_CLARITY",
            DEFAULT_AUTO_FIX_CLARITY,
        )
    )

    def __post_init__(self) -> None:
        """Validate config values after construction."""
        if not 0.0 <= self.min_quality_score <= 1.0:
            raise ValueError("min_quality_score must be between 0.0 and 1.0")
        if self.max_flags_allowed <= 0:
            raise ValueError("max_flags_allowed must be positive")


class _CrewAIStub:
    """Simple fallback used when CrewAI cannot be imported safely."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _AgentStub(_CrewAIStub):
    """Fallback agent container."""


class _TaskStub(_CrewAIStub):
    """Fallback task container."""


class _CrewStub(_CrewAIStub):
    """Fallback crew container that produces a deterministic QA report."""

    def kickoff(self, *args: Any, **kwargs: Any) -> str:
        """Return a valid final report JSON payload when real CrewAI is disabled."""
        inputs = kwargs.get("inputs", {})
        context_json = str(inputs.get("context_json") or "")
        config = self.kwargs.get("qa_config") or QAConfig()
        report = _build_final_report_from_context_json(context_json, config)
        return report.model_dump_json()


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse a boolean environment variable with a sensible default."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _using_real_crewai() -> bool:
    """Return True when the real CrewAI runtime is explicitly enabled."""
    return os.getenv(REAL_CREW_ENV_VAR, "false").lower() == "true"


def _load_crewai_classes() -> tuple[type[Any], type[Any], type[Any]]:
    """Import CrewAI safely, or fall back to lightweight stubs."""
    if not _using_real_crewai():
        return _AgentStub, _TaskStub, _CrewStub

    try:
        from crewai import Agent, Crew, Task

        return Agent, Task, Crew
    except Exception as exc:  # pragma: no cover
        logger.warning("CrewAI import failed, using fallback stubs: %s", exc)
        return _AgentStub, _TaskStub, _CrewStub


def create_qa_agent(config: QAConfig) -> Any:
    """Create the CrewAI QA agent definition."""
    Agent, _, _ = _load_crewai_classes()
    return Agent(
        role="Senior QA Editor",
        goal=(
            "Fact-check every claim against source list, fix grammar and clarity "
            "issues, assign a quality score, and return a publication-ready report"
        ),
        backstory=(
            "A meticulous editor with a background in both journalism and "
            "technical writing who never lets an uncited claim slip through "
            "and always pushes reports toward publication-ready quality."
        ),
        verbose=True,
        allow_delegation=False,
        llm=config.model_name,
    )


def create_qa_task(agent: Any) -> Any:
    """Create the CrewAI task definition for the QA agent."""
    _, Task, _ = _load_crewai_classes()
    expected_output = json.dumps(FinalReport.model_json_schema(), indent=2)
    return Task(
        description=(
            "Read the combined QA context JSON in `{context_json}` containing the full "
            "ReportDraft and the original FindingsOutput sources. For each "
            "section, verify that the claims are supported by the cited "
            "sources, flag factual inaccuracies, missing citations, grammar "
            "issues, or unclear prose, auto-correct grammar and clarity "
            "problems where possible, produce a final polished markdown "
            "document, assign a quality_score from 0.0 to 1.0, and set "
            "qa_passed=true only if all flags are resolved. Return strict JSON "
            "matching the FinalReport schema."
        ),
        expected_output=expected_output,
        agent=agent,
    )


def _build_final_report_from_context_json(
    context_json: str,
    config: QAConfig,
) -> FinalReport:
    """Create a deterministic final report from serialized draft and findings data."""
    raw_context = json.loads(context_json)
    draft = ReportDraft.model_validate(raw_context["draft"])
    findings = FindingsOutput.model_validate(raw_context["findings"])
    return _build_final_report_from_draft(draft, findings, config)


def _build_final_report_from_draft(
    draft: ReportDraft,
    findings: FindingsOutput,
    config: QAConfig,
) -> FinalReport:
    """Build a deterministic QA-approved report from draft and findings data."""
    source_lookup = {source.url: source for source in findings.sources}
    polished_sections: list[SectionDraft] = []
    qa_flags: list[QAFlag] = []

    for section in draft.sections:
        polished_content = section.content

        if not section.citations:
            qa_flags.append(
                QAFlag(
                    section_number=section.section_number,
                    issue_type="citation_missing",
                    description="Section does not include any citations.",
                    resolved=False,
                    original_text=_snippet(section.content),
                    corrected_text=None,
                )
            )

        invalid_citations = [
            citation
            for citation in section.citations
            if citation.url not in source_lookup
        ]
        for citation in invalid_citations:
            qa_flags.append(
                QAFlag(
                    section_number=section.section_number,
                    issue_type="factual",
                    description=(
                        "Section cites a source URL that is not present in the "
                        "research findings."
                    ),
                    resolved=False,
                    original_text=_snippet(section.content),
                    corrected_text=None,
                )
            )

        corrected_content = _apply_auto_fixes(
            text=polished_content,
            auto_fix_grammar=config.auto_fix_grammar,
            auto_fix_clarity=config.auto_fix_clarity,
        )
        if corrected_content != polished_content:
            issue_type = "grammar" if config.auto_fix_grammar else "clarity"
            qa_flags.append(
                QAFlag(
                    section_number=section.section_number,
                    issue_type=issue_type,
                    description=(
                        "QA normalized phrasing, spacing, or punctuation "
                        "for readability."
                    ),
                    resolved=True,
                    original_text=_snippet(polished_content),
                    corrected_text=_snippet(corrected_content),
                )
            )
            polished_content = corrected_content

        polished_sections.append(
            section.model_copy(
                update={
                    "content": polished_content,
                    "word_count": count_words(polished_content),
                }
            )
        )

    polished_summary = _apply_auto_fixes(
        text=draft.executive_summary,
        auto_fix_grammar=config.auto_fix_grammar,
        auto_fix_clarity=config.auto_fix_clarity,
    )
    total_word_count = sum(section.word_count for section in polished_sections)
    polished_draft = draft.model_copy(
        update={
            "executive_summary": polished_summary,
            "sections": polished_sections,
            "total_word_count": total_word_count,
        }
    )
    markdown_output = assemble_markdown(polished_draft)
    quality_score = _calculate_quality_score(qa_flags, config.max_flags_allowed)

    return FinalReport.model_validate(
        {
            "topic": draft.topic,
            "report_type": draft.report_type,
            "executive_summary": polished_summary,
            "markdown_output": markdown_output,
            "total_word_count": total_word_count,
            "all_citations": [
                citation.model_dump() for citation in draft.all_citations
            ],
            "qa_flags": [flag.model_dump() for flag in qa_flags],
            "qa_passed": not any(not flag.resolved for flag in qa_flags),
            "quality_score": quality_score,
            "job_id": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def _apply_auto_fixes(
    text: str,
    auto_fix_grammar: bool,
    auto_fix_clarity: bool,
) -> str:
    """Apply lightweight automatic grammar and clarity cleanups."""
    corrected_text = text
    if auto_fix_grammar:
        corrected_text = re.sub(r"[ \t]+", " ", corrected_text)
        corrected_text = re.sub(r"\s+([,.;:!?])", r"\1", corrected_text)
        corrected_text = re.sub(r"\n{3,}", "\n\n", corrected_text)

    if auto_fix_clarity:
        corrected_text = corrected_text.replace(
            "This section explains",
            "This section covers",
        )
        corrected_text = corrected_text.replace(
            "This section develops",
            "This section outlines",
        )

    return corrected_text.strip()


def _calculate_quality_score(qa_flags: list[QAFlag], max_flags_allowed: int) -> float:
    """Calculate a normalized quality score from the QA flag set."""
    unresolved_flags = sum(1 for flag in qa_flags if not flag.resolved)
    resolved_flags = len(qa_flags) - unresolved_flags
    overflow_flags = max(0, len(qa_flags) - max_flags_allowed)
    score = (
        1.0
        - (unresolved_flags * 0.25)
        - (resolved_flags * 0.05)
        - (overflow_flags * 0.05)
    )
    return max(0.0, min(1.0, round(score, 2)))


def _snippet(text: str) -> str:
    """Return a short, readable text snippet for QA flag metadata."""
    normalized_text = " ".join(text.split())
    return normalized_text[:SECTION_SNIPPET_LENGTH]


def _normalize_raw_output(raw_output: Any) -> str:
    """Convert CrewAI output into a JSON string suitable for validation."""
    if hasattr(raw_output, "raw"):
        raw_output = raw_output.raw
    if isinstance(raw_output, dict):
        return json.dumps(raw_output)
    if isinstance(raw_output, FinalReport):
        return raw_output.model_dump_json()

    normalized_output = str(raw_output).strip()
    if normalized_output.startswith("```"):
        output_lines = normalized_output.splitlines()
        if output_lines:
            output_lines = output_lines[1:]
        if output_lines and output_lines[-1].strip() == "```":
            output_lines = output_lines[:-1]
        normalized_output = "\n".join(output_lines).strip()
    return normalized_output


def _validate_report_sources(findings: FindingsOutput, report: FinalReport) -> None:
    """Ensure citations in the final report are sourced from the findings."""
    allowed_sources = {source.url for source in findings.sources}
    invalid_sources = [
        citation.url
        for citation in report.all_citations
        if citation.url not in allowed_sources
    ]
    if invalid_sources:
        raise QAError(
            "QA output referenced URLs not present in findings: "
            f"{sorted(set(invalid_sources))}"
        )


def run_qa(draft: ReportDraft, findings: FindingsOutput) -> FinalReport:
    """Run the QA agent and return a validated final report."""
    config = QAConfig()
    Agent, Task, Crew = _load_crewai_classes()

    try:
        context_json = json.dumps(
            {
                "draft": draft.model_dump(mode="json"),
                "findings": findings.model_dump(mode="json"),
            }
        )
        qa_agent = create_qa_agent(config)
        qa_task = create_qa_task(qa_agent)

        crew_kwargs: dict[str, Any] = {
            "agents": [qa_agent] if Agent is not _AgentStub else [qa_agent],
            "tasks": [qa_task] if Task is not _TaskStub else [qa_task],
            "verbose": True,
        }
        if Crew is _CrewStub:
            crew_kwargs["qa_config"] = config

        crew = Crew(**crew_kwargs)
        raw_output = crew.kickoff(inputs={"context_json": context_json})
        report = FinalReport.model_validate_json(_normalize_raw_output(raw_output))
        _validate_report_sources(findings, report)

        if report.quality_score < config.min_quality_score:
            flag_summary = [
                (
                    f"section={flag.section_number}:{flag.issue_type}:"
                    f"resolved={flag.resolved}"
                )
                for flag in report.qa_flags
            ]
            raise QAError(
                "QA quality score below threshold: "
                f"score={report.quality_score} min={config.min_quality_score} "
                f"flags={flag_summary}"
            )

        resolved_count = sum(1 for flag in report.qa_flags if flag.resolved)
        logger.info(
            "QA completed topic=%s flags=%s resolved=%s quality_score=%.2f",
            report.topic,
            len(report.qa_flags),
            resolved_count,
            report.quality_score,
        )
        return report
    except QAError:
        raise
    except Exception as exc:
        logger.exception("QA pipeline failed for topic=%s", draft.topic)
        raise QAError(
            "QA pipeline failed for topic "
            f"'{draft.topic}' with citations={len(draft.all_citations)}: {exc}"
        ) from exc
