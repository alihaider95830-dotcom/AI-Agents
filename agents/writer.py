from __future__ import annotations

import json
import logging
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import appdirs
except ImportError:  # pragma: no cover - depends on environment
    appdirs = None

from exceptions import WriterError
from schemas.draft import CitationItem, ReportDraft, SectionDraft, count_words
from schemas.findings import FindingsOutput
from schemas.outline import ReportOutline, SectionItem

logger = logging.getLogger(__name__)
CREWAI_LOCALAPPDATA_ENV_VAR = "WRITER_CREWAI_LOCALAPPDATA"
REAL_CREW_ENV_VAR = "WRITER_USE_REAL_CREWAI"
DEFAULT_WRITER_MODEL = "gpt-4o-mini"
DEFAULT_WORD_COUNT_TOLERANCE = 0.20
DEFAULT_CITATION_STYLE = "inline"
DEFAULT_OUTPUT_FORMAT = "markdown"
DEFAULT_STREAM_SECTIONS = True
WORDS_PER_MINUTE = 200

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
class WriterConfig:
    """Runtime configuration for the Writer agent."""

    model_name: str = field(
        default_factory=lambda: os.getenv("WRITER_MODEL_NAME", DEFAULT_WRITER_MODEL)
    )
    word_count_tolerance: float = field(
        default_factory=lambda: float(
            os.getenv("WRITER_WORD_COUNT_TOLERANCE", DEFAULT_WORD_COUNT_TOLERANCE)
        )
    )
    citation_style: str = field(
        default_factory=lambda: os.getenv("WRITER_CITATION_STYLE", DEFAULT_CITATION_STYLE)
    )
    output_format: str = field(
        default_factory=lambda: os.getenv("WRITER_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)
    )
    stream_sections: bool = field(
        default_factory=lambda: _parse_bool_env("WRITER_STREAM_SECTIONS", DEFAULT_STREAM_SECTIONS)
    )

    def __post_init__(self) -> None:
        """Validate config values after construction."""
        if not 0 <= self.word_count_tolerance <= 1:
            raise ValueError("word_count_tolerance must be between 0 and 1")
        if not self.citation_style.strip():
            raise ValueError("citation_style must not be blank")
        if not self.output_format.strip():
            raise ValueError("output_format must not be blank")


class _CrewAIStub:
    """Simple fallback used when CrewAI cannot be imported safely."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _AgentStub(_CrewAIStub):
    """Fallback agent container."""


class _TaskStub(_CrewAIStub):
    """Fallback task container."""


class _CrewStub(_CrewAIStub):
    """Fallback crew container that produces a deterministic report draft."""

    def kickoff(self, *args: Any, **kwargs: Any) -> str:
        """Return a valid draft JSON payload when real CrewAI is disabled."""
        inputs = kwargs.get("inputs", {})
        context_json = str(inputs.get("context_json") or "")
        config = self.kwargs.get("writer_config") or WriterConfig()
        draft = _build_draft_from_context_json(context_json, config)
        return draft.model_dump_json()


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


def create_writer_agent(config: WriterConfig) -> Any:
    """Create the CrewAI writer agent definition."""
    Agent, _, _ = _load_crewai_classes()
    return Agent(
        role="Professional Report Writer",
        goal="Draft each report section with precision, proper citations, and engaging prose",
        backstory=(
            "A senior technical writer who excels at turning structured outlines into polished, "
            "well-cited long-form content with a consistent voice and clear narrative flow."
        ),
        verbose=True,
        allow_delegation=False,
        llm=config.model_name,
    )


def create_writer_task(agent: Any) -> Any:
    """Create the CrewAI task definition for the writer."""
    _, Task, _ = _load_crewai_classes()
    expected_output = json.dumps(ReportDraft.model_json_schema(), indent=2)
    return Task(
        description=(
            "Read the combined writer context JSON in `{context_json}` containing a ReportOutline "
            "and FindingsOutput. Iterate through each SectionItem in the outline, draft section "
            "content that respects the argument, key_points, and target_word_count, insert inline "
            "numeric citations like [1] whenever sources are used, produce markdown-ready prose "
            "with ## headings and bullet points where helpful, and assemble a full markdown "
            "document with a references section at the end. Return strict JSON matching the "
            "ReportDraft schema."
        ),
        expected_output=expected_output,
        agent=agent,
    )


def assemble_markdown(draft: ReportDraft) -> str:
    """Assemble a clean markdown document from a validated report draft."""
    estimated_read_time = max(1, math.ceil(draft.total_word_count / WORDS_PER_MINUTE))
    lines = [
        f"# {draft.topic}",
        f"**Type:** {draft.report_type}",
        f"**Estimated read time:** {estimated_read_time} min",
        "",
        "## Executive Summary",
        draft.executive_summary,
        "",
    ]

    for section in draft.sections:
        lines.extend(
            [
                f"## {section.title}",
                section.content,
                "",
            ]
        )

    lines.append("## References")
    if draft.all_citations:
        lines.extend(citation.inline_reference for citation in draft.all_citations)
    else:
        lines.append("No references provided.")

    return "\n".join(lines).strip()


def _build_draft_from_context_json(
    context_json: str,
    config: WriterConfig,
) -> ReportDraft:
    """Create a deterministic draft from serialized outline and findings data."""
    raw_context = json.loads(context_json)
    outline = ReportOutline.model_validate(raw_context["outline"])
    findings = FindingsOutput.model_validate(raw_context["findings"])
    return _build_draft_from_outline(outline, findings, config)


def _build_draft_from_outline(
    outline: ReportOutline,
    findings: FindingsOutput,
    config: WriterConfig,
) -> ReportDraft:
    """Build a deterministic report draft from validated outline and findings data."""
    source_lookup = {source.url: source for source in findings.sources}
    citation_index_by_url: dict[str, int] = {}
    all_citations: list[CitationItem] = []
    sections: list[SectionDraft] = []
    section_targets = {
        section.section_number: section.target_word_count for section in outline.sections
    }

    for section in outline.sections:
        section_citations = _build_section_citations(
            section=section,
            source_lookup=source_lookup,
            citation_index_by_url=citation_index_by_url,
            all_citations=all_citations,
        )
        section_content = _build_section_content(
            outline=outline,
            findings=findings,
            section=section,
            citations=section_citations,
        )
        section_word_count = count_words(section_content)
        sections.append(
            SectionDraft.model_validate(
                {
                    "section_number": section.section_number,
                    "title": section.title,
                    "content": section_content,
                    "word_count": section_word_count,
                    "citations": [citation.model_dump() for citation in section_citations],
                    "within_word_target": _is_within_word_target(
                        actual_words=section_word_count,
                        target_words=section.target_word_count,
                        tolerance=config.word_count_tolerance,
                    ),
                },
                context={
                    "target_word_count": section.target_word_count,
                    "word_count_tolerance": config.word_count_tolerance,
                },
            )
        )

    total_word_count = sum(section.word_count for section in sections)
    markdown_output = _assemble_markdown_parts(
        topic=outline.topic,
        report_type=outline.report_type,
        executive_summary=outline.executive_summary,
        sections=sections,
        citations=all_citations,
        total_word_count=total_word_count,
    )

    return ReportDraft.model_validate(
        {
            "topic": outline.topic,
            "report_type": outline.report_type,
            "executive_summary": outline.executive_summary,
            "sections": [section.model_dump() for section in sections],
            "total_word_count": total_word_count,
            "all_citations": [citation.model_dump() for citation in all_citations],
            "markdown_output": markdown_output,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        context={
            "section_targets": section_targets,
            "word_count_tolerance": config.word_count_tolerance,
        },
    )


def _build_section_citations(
    section: SectionItem,
    source_lookup: dict[str, Any],
    citation_index_by_url: dict[str, int],
    all_citations: list[CitationItem],
) -> list[CitationItem]:
    """Build a section-level citation list while maintaining a deduplicated master list."""
    citations: list[CitationItem] = []
    seen_urls: set[str] = set()

    for url in section.suggested_sources:
        source = source_lookup.get(url)
        if source is None or url in seen_urls:
            continue

        if url not in citation_index_by_url:
            citation_index_by_url[url] = len(citation_index_by_url) + 1
            all_citations.append(
                CitationItem(
                    index=citation_index_by_url[url],
                    url=source.url,
                    title=source.title,
                    inline_reference=_format_inline_reference(
                        citation_index_by_url[url],
                        source.title,
                        source.url,
                    ),
                )
            )

        citations.append(
            CitationItem(
                index=citation_index_by_url[url],
                url=source.url,
                title=source.title,
                inline_reference=_format_inline_reference(
                    citation_index_by_url[url],
                    source.title,
                    source.url,
                ),
            )
        )
        seen_urls.add(url)

    return citations


def _build_section_content(
    outline: ReportOutline,
    findings: FindingsOutput,
    section: SectionItem,
    citations: list[CitationItem],
) -> str:
    """Generate markdown-ready section content that stays close to the section target."""
    citation_tokens = [f"[{citation.index}]" for citation in citations]
    fact_pool = findings.key_facts or [
        f"The research collected for {outline.topic} points to recurring operational patterns."
    ]
    lead_citation = f" {citation_tokens[0]}" if citation_tokens else ""
    lines = [
        (
            f"{section.argument} This section develops the report's narrative around "
            f"{section.title.lower()} and keeps the focus on {outline.topic}.{lead_citation}"
        ),
        "",
    ]

    for point_index, key_point in enumerate(section.key_points):
        citation_token = (
            f" {citation_tokens[point_index % len(citation_tokens)]}"
            if citation_tokens
            else ""
        )
        lines.append(f"- {key_point}{citation_token}")

    lines.append("")
    paragraph_index = 0
    content = "\n".join(lines).strip()

    while count_words(content) < section.target_word_count:
        fact = fact_pool[paragraph_index % len(fact_pool)]
        citation_token = (
            f" {citation_tokens[paragraph_index % len(citation_tokens)]}"
            if citation_tokens
            else ""
        )
        lines.append(
            (
                f"The evidence shows that {fact.lower()} This reinforces the section's argument "
                f"and clarifies why the topic matters in practice.{citation_token}"
            )
        )
        lines.append("")
        content = "\n".join(lines).strip()
        paragraph_index += 1

        if paragraph_index > max(6, len(fact_pool) * 2):
            break

    return content


def _assemble_markdown_parts(
    topic: str,
    report_type: str,
    executive_summary: str,
    sections: list[SectionDraft],
    citations: list[CitationItem],
    total_word_count: int,
) -> str:
    """Assemble markdown from primitive parts for draft construction."""
    draft = ReportDraft.model_construct(
        topic=topic,
        report_type=report_type,
        executive_summary=executive_summary,
        sections=sections,
        total_word_count=total_word_count,
        all_citations=citations,
        markdown_output="placeholder",
        timestamp=datetime.now(timezone.utc),
    )
    return assemble_markdown(draft)


def _format_inline_reference(index: int, title: str, url: str) -> str:
    """Format a citation entry for inline references and the references section."""
    return f"[{index}] {title} - {url}"


def _is_within_word_target(
    actual_words: int,
    target_words: int,
    tolerance: float,
) -> bool:
    """Return True when the actual word count is within the allowed tolerance."""
    minimum_words = target_words * (1 - tolerance)
    maximum_words = target_words * (1 + tolerance)
    return minimum_words <= actual_words <= maximum_words


def _normalize_raw_output(raw_output: Any) -> str:
    """Convert CrewAI output into a JSON string suitable for validation."""
    if hasattr(raw_output, "raw"):
        raw_output = raw_output.raw
    if isinstance(raw_output, dict):
        return json.dumps(raw_output)
    if isinstance(raw_output, ReportDraft):
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


def _validate_writer_sources(findings: FindingsOutput, draft: ReportDraft) -> None:
    """Ensure all citations point to source URLs provided by the researcher."""
    allowed_sources = {source.url for source in findings.sources}
    invalid_sources = [
        citation.url for citation in draft.all_citations if citation.url not in allowed_sources
    ]
    if invalid_sources:
        raise WriterError(
            "Writer output referenced URLs not present in findings: "
            f"{sorted(set(invalid_sources))}"
        )


def run_writer(outline: ReportOutline, findings: FindingsOutput) -> ReportDraft:
    """Run the Writer agent and return a validated report draft."""
    config = WriterConfig()
    Agent, Task, Crew = _load_crewai_classes()
    section_targets = {
        section.section_number: section.target_word_count for section in outline.sections
    }

    try:
        context_json = json.dumps(
            {
                "outline": outline.model_dump(mode="json"),
                "findings": findings.model_dump(mode="json"),
            }
        )
        writer_agent = create_writer_agent(config)
        writer_task = create_writer_task(writer_agent)

        crew_kwargs: dict[str, Any] = {
            "agents": [writer_agent] if Agent is not _AgentStub else [writer_agent],
            "tasks": [writer_task] if Task is not _TaskStub else [writer_task],
            "verbose": True,
        }
        if Crew is _CrewStub:
            crew_kwargs["writer_config"] = config

        crew = Crew(**crew_kwargs)
        raw_output = crew.kickoff(inputs={"context_json": context_json})
        draft = ReportDraft.model_validate_json(
            _normalize_raw_output(raw_output),
            context={
                "section_targets": section_targets,
                "word_count_tolerance": config.word_count_tolerance,
            },
        )
        _validate_writer_sources(findings, draft)

        for section in draft.sections:
            logger.info(
                "Writer completed section=%s title=%s word_count=%s citations=%s",
                section.section_number,
                section.title,
                section.word_count,
                len(section.citations),
            )

        return draft
    except WriterError:
        raise
    except Exception as exc:
        logger.exception("Writer pipeline failed for topic=%s", outline.topic)
        raise WriterError(
            "Writer pipeline failed for topic "
            f"'{outline.topic}' with sections={[section.title for section in outline.sections]}: {exc}"
        ) from exc
