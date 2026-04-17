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

from exceptions import PlannerError
from schemas.findings import FindingsOutput
from schemas.outline import ReportOutline, SectionItem

logger = logging.getLogger(__name__)
CREWAI_LOCALAPPDATA_ENV_VAR = "PLANNER_CREWAI_LOCALAPPDATA"
REAL_CREW_ENV_VAR = "PLANNER_USE_REAL_CREWAI"
DEFAULT_PLANNER_MODEL = "gpt-4o-mini"
DEFAULT_MIN_SECTIONS = 4
DEFAULT_MAX_SECTIONS = 8
DEFAULT_WORDS_PER_SECTION = 300
DEFAULT_REPORT_TYPES = [
    "analytical",
    "informational",
    "comparative",
    "argumentative",
]
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
class PlannerConfig:
    """Runtime configuration for the Planner agent."""

    model_name: str = field(
        default_factory=lambda: os.getenv("PLANNER_MODEL_NAME", DEFAULT_PLANNER_MODEL)
    )
    min_sections: int = field(
        default_factory=lambda: int(os.getenv("PLANNER_MIN_SECTIONS", DEFAULT_MIN_SECTIONS))
    )
    max_sections: int = field(
        default_factory=lambda: int(os.getenv("PLANNER_MAX_SECTIONS", DEFAULT_MAX_SECTIONS))
    )
    default_words_per_section: int = field(
        default_factory=lambda: int(
            os.getenv(
                "PLANNER_DEFAULT_WORDS_PER_SECTION",
                DEFAULT_WORDS_PER_SECTION,
            )
        )
    )
    report_types: list[str] = field(
        default_factory=lambda: [
            item.strip()
            for item in os.getenv(
                "PLANNER_REPORT_TYPES",
                ",".join(DEFAULT_REPORT_TYPES),
            ).split(",")
            if item.strip()
        ]
    )

    def __post_init__(self) -> None:
        """Validate config bounds after construction."""
        if not DEFAULT_MIN_SECTIONS <= self.min_sections <= self.max_sections <= DEFAULT_MAX_SECTIONS:
            raise ValueError(
                f"section bounds must satisfy {DEFAULT_MIN_SECTIONS} <= min_sections "
                f"<= max_sections <= {DEFAULT_MAX_SECTIONS}"
            )
        if self.default_words_per_section < 100:
            raise ValueError("default_words_per_section must be at least 100")
        if not self.report_types:
            raise ValueError("report_types must contain at least one value")


class _CrewAIStub:
    """Simple fallback used when CrewAI cannot be imported safely."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _AgentStub(_CrewAIStub):
    """Fallback agent container."""


class _TaskStub(_CrewAIStub):
    """Fallback task container."""


class _CrewStub(_CrewAIStub):
    """Fallback crew container that produces a deterministic outline."""

    def kickoff(self, *args: Any, **kwargs: Any) -> str:
        """Return a valid outline JSON payload when real CrewAI is disabled."""
        inputs = kwargs.get("inputs", {})
        findings_json = str(inputs.get("findings_json") or "")
        config = self.kwargs.get("planner_config") or PlannerConfig()
        outline = _build_outline_from_findings_json(findings_json, config)
        return outline.model_dump_json()


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


def _choose_report_type(findings: FindingsOutput, config: PlannerConfig) -> str:
    """Determine the most appropriate report type from the findings."""
    query_text = findings.query.lower()
    key_fact_text = " ".join(findings.key_facts).lower()

    if any(token in query_text for token in ("vs", "versus", "compare", "comparison")):
        preferred_type = "comparative"
    elif any(token in query_text for token in ("should", "must", "why", "case for", "debate")):
        preferred_type = "argumentative"
    elif any(token in query_text for token in ("overview", "guide", "what is", "introduction")):
        preferred_type = "informational"
    elif any(token in key_fact_text for token in ("increase", "decline", "trend", "impact", "risk")):
        preferred_type = "analytical"
    else:
        preferred_type = "analytical"

    if preferred_type in config.report_types:
        return preferred_type
    return config.report_types[0]


def _target_section_count(findings: FindingsOutput, config: PlannerConfig) -> int:
    """Choose a section count based on the research density."""
    density_score = max(len(findings.key_facts), len(findings.sources) // 2)
    suggested_count = config.min_sections + math.ceil(density_score / 3)
    return max(config.min_sections, min(config.max_sections, suggested_count))


def _report_blueprints() -> dict[str, list[tuple[str, str]]]:
    """Return reusable section blueprints for each report type."""
    return {
        "analytical": [
            ("Introduction and Framing", "Define the core question and why the topic matters now."),
            ("Current Landscape", "Summarize the present state of the topic using the clearest evidence."),
            ("Key Findings", "Synthesize the strongest research findings into a structured narrative."),
            ("Drivers and Dynamics", "Explain the forces shaping the topic and how they interact."),
            ("Risks and Tradeoffs", "Assess meaningful risks, limitations, and unresolved tensions."),
            ("Strategic Implications", "Translate the findings into practical implications for stakeholders."),
            ("Future Outlook", "Project what is likely to happen next and what to watch."),
            ("Conclusion", "Reinforce the central takeaway and close with a synthesis."),
        ],
        "informational": [
            ("Introduction", "Introduce the topic and orient the reader."),
            ("Background and Context", "Provide the essential background before diving deeper."),
            ("Core Concepts", "Explain the major ideas, mechanisms, or components involved."),
            ("Key Findings", "Present the most relevant evidence in a clear structure."),
            ("Practical Applications", "Show how the topic appears in real-world settings."),
            ("Challenges and Limitations", "Clarify the main caveats and open questions."),
            ("What to Watch", "Highlight emerging developments and signals worth monitoring."),
            ("Conclusion", "Summarize the main points with a clear closing takeaway."),
        ],
        "comparative": [
            ("Introduction and Comparison Lens", "Define what is being compared and the criteria used."),
            ("Option A Profile", "Describe the first option's strengths, limitations, and evidence base."),
            ("Option B Profile", "Describe the second option's strengths, limitations, and evidence base."),
            ("Similarity Analysis", "Identify meaningful overlaps and shared constraints."),
            ("Difference Analysis", "Explain the most important differences and why they matter."),
            ("Decision Criteria", "Connect the comparison back to stakeholder priorities."),
            ("Recommendation", "State which option fits which context, backed by the research."),
            ("Conclusion", "Close with the clearest high-level comparison takeaway."),
        ],
        "argumentative": [
            ("Introduction and Thesis", "State the central claim, scope, and why it matters."),
            ("Context and Stakes", "Explain the background conditions and what is at stake."),
            ("Supporting Evidence", "Present the strongest evidence in favor of the thesis."),
            ("Counterarguments", "Surface the main objections or competing interpretations fairly."),
            ("Rebuttal and Synthesis", "Respond to counterarguments and strengthen the overall case."),
            ("Implications", "Describe what follows if the argument is accepted."),
            ("Actionable Recommendation", "Translate the argument into a clear next step."),
            ("Conclusion", "Reaffirm the thesis and the strongest reason it holds."),
        ],
    }


def _select_blueprint(report_type: str, section_count: int) -> list[tuple[str, str]]:
    """Return the ordered blueprint truncated to the requested section count."""
    blueprints = _report_blueprints()
    selected_blueprint = blueprints.get(report_type, blueprints["analytical"])
    return selected_blueprint[:section_count]


def _slice_with_wrap(items: list[str], start_index: int, count: int) -> list[str]:
    """Select a deterministic window from a list with wraparound."""
    if not items:
        return []

    selected_items: list[str] = []
    for offset in range(count):
        item = items[(start_index + offset) % len(items)]
        if item not in selected_items:
            selected_items.append(item)
    return selected_items


def _build_key_points(
    findings: FindingsOutput,
    section_title: str,
    section_argument: str,
    section_index: int,
) -> list[str]:
    """Create writer-facing key points for a section."""
    selected_facts = _slice_with_wrap(findings.key_facts, section_index, 2)
    key_points = [
        f"Anchor the section around this angle: {section_argument}",
        f"Connect the discussion explicitly back to the report topic: {findings.query}.",
    ]

    for fact in selected_facts:
        key_points.append(f"Use this evidence in {section_title}: {fact}")

    if len(key_points) < 3:
        key_points.append(
            "Summarize the strongest supporting evidence before transitioning to the next section."
        )
    return key_points[:5]


def _build_section_word_count(
    config: PlannerConfig,
    section_title: str,
    section_index: int,
    total_sections: int,
) -> int:
    """Assign word counts based on section role and complexity."""
    base_words = config.default_words_per_section
    normalized_title = section_title.casefold()

    if section_index == 0 or section_index == total_sections - 1:
        multiplier = 0.8
    elif "key findings" in normalized_title or "difference analysis" in normalized_title:
        multiplier = 1.2
    elif "drivers" in normalized_title or "implications" in normalized_title:
        multiplier = 1.15
    else:
        multiplier = 1.0

    return max(100, int(round(base_words * multiplier)))


def _build_executive_summary(
    findings: FindingsOutput,
    report_type: str,
    section_count: int,
) -> str:
    """Create a concise overview of the report structure."""
    return (
        f"This {report_type} report on {findings.query} organizes the research into "
        f"{section_count} sections that move from context to evidence and implications. "
        "It prioritizes the strongest findings, maps supporting sources to each section, "
        "and gives the writer a clear structure to execute."
    )


def _build_outline_from_findings(findings: FindingsOutput, config: PlannerConfig) -> ReportOutline:
    """Generate a valid report outline from validated findings."""
    report_type = _choose_report_type(findings, config)
    section_count = _target_section_count(findings, config)
    blueprint = _select_blueprint(report_type, section_count)
    source_urls = [source.url for source in findings.sources]

    sections: list[SectionItem] = []
    for section_index, (title, argument) in enumerate(blueprint, start=1):
        sections.append(
            SectionItem(
                section_number=section_index,
                title=title,
                argument=argument,
                key_points=_build_key_points(findings, title, argument, section_index - 1),
                suggested_sources=_slice_with_wrap(
                    source_urls,
                    section_index - 1,
                    min(3, len(source_urls)),
                ),
                target_word_count=_build_section_word_count(
                    config=config,
                    section_title=title,
                    section_index=section_index - 1,
                    total_sections=len(blueprint),
                ),
            )
        )

    total_target_words = sum(section.target_word_count for section in sections)
    estimated_read_time_minutes = max(1, math.ceil(total_target_words / WORDS_PER_MINUTE))

    return ReportOutline(
        topic=findings.query,
        report_type=report_type,
        executive_summary=_build_executive_summary(findings, report_type, len(sections)),
        sections=sections,
        total_target_words=total_target_words,
        estimated_read_time_minutes=estimated_read_time_minutes,
        timestamp=datetime.now(timezone.utc),
    )


def _build_outline_from_findings_json(
    findings_json: str,
    config: PlannerConfig,
) -> ReportOutline:
    """Create a deterministic outline from serialized findings."""
    findings = FindingsOutput.model_validate_json(findings_json)
    return _build_outline_from_findings(findings, config)


def create_planner_agent(config: PlannerConfig) -> Any:
    """Create the CrewAI planner agent definition."""
    Agent, _, _ = _load_crewai_classes()
    return Agent(
        role="Strategic Report Planner",
        goal="Transform raw research findings into a coherent, well-structured report outline",
        backstory=(
            "An experienced editor who specializes in turning dense research into logical, "
            "reader-friendly narrative structures that writers can execute with confidence."
        ),
        verbose=True,
        allow_delegation=False,
        llm=config.model_name,
    )


def create_planner_task(agent: Any) -> Any:
    """Create the CrewAI task definition for the planner."""
    _, Task, _ = _load_crewai_classes()
    expected_output = json.dumps(ReportOutline.model_json_schema(), indent=2)
    return Task(
        description=(
            "Read the FindingsOutput JSON provided in `{findings_json}`. Determine the best "
            "report_type based on the topic and key_facts, then produce 4-8 sections with a "
            "logical narrative flow. Assign target word counts per section based on complexity, "
            "map relevant source URLs from the findings to each section, and return strict JSON "
            "matching the ReportOutline schema."
        ),
        expected_output=expected_output,
        agent=agent,
    )


def _normalize_raw_output(raw_output: Any) -> str:
    """Convert CrewAI output into a JSON string suitable for validation."""
    if hasattr(raw_output, "raw"):
        raw_output = raw_output.raw
    if isinstance(raw_output, dict):
        return json.dumps(raw_output)
    if isinstance(raw_output, ReportOutline):
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


def _validate_suggested_sources(findings: FindingsOutput, outline: ReportOutline) -> None:
    """Ensure outlined source URLs are drawn from the findings."""
    allowed_sources = {source.url for source in findings.sources}
    invalid_sources = [
        source_url
        for section in outline.sections
        for source_url in section.suggested_sources
        if source_url not in allowed_sources
    ]
    if invalid_sources:
        raise PlannerError(
            "Planner output referenced URLs not present in findings: "
            f"{sorted(set(invalid_sources))}"
        )


def run_planner(findings: FindingsOutput) -> ReportOutline:
    """Run the Planner agent and return a validated report outline."""
    config = PlannerConfig()
    Agent, Task, Crew = _load_crewai_classes()

    try:
        findings_json = findings.model_dump_json()
        planner_agent = create_planner_agent(config)
        planner_task = create_planner_task(planner_agent)

        crew_kwargs: dict[str, Any] = {
            "agents": [planner_agent] if Agent is not _AgentStub else [planner_agent],
            "tasks": [planner_task] if Task is not _TaskStub else [planner_task],
            "verbose": True,
        }
        if Crew is _CrewStub:
            crew_kwargs["planner_config"] = config

        crew = Crew(**crew_kwargs)
        raw_output = crew.kickoff(inputs={"findings_json": findings_json})
        outline = ReportOutline.model_validate_json(_normalize_raw_output(raw_output))
        _validate_suggested_sources(findings, outline)
        logger.info(
            "Planner produced outline for topic=%s sections=%s total_target_words=%s report_type=%s",
            findings.query,
            len(outline.sections),
            outline.total_target_words,
            outline.report_type,
        )
        return outline
    except PlannerError:
        raise
    except Exception as exc:
        logger.exception("Planner pipeline failed for topic=%s", findings.query)
        raise PlannerError(
            "Planner pipeline failed for topic "
            f"'{findings.query}' with findings={findings.model_dump(mode='json')}: {exc}"
        ) from exc
