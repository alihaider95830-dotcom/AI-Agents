from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock, call

import pytest
from pydantic import ValidationError

from agents import pipeline, planner
from exceptions import PlannerError
from schemas.findings import FindingsOutput
from schemas.outline import ReportOutline

FAKE_TOPIC = "AI agents in enterprise support operations"


def _mock_findings() -> FindingsOutput:
    return FindingsOutput(
        query=FAKE_TOPIC,
        sources=[
            {
                "url": f"https://example.com/source-{index}",
                "title": f"Source {index}",
                "snippet": f"Snippet {index}",
                "scrape_success": True,
            }
            for index in range(1, 11)
        ],
        key_facts=[
            "AI copilots reduce first-response times in customer support workflows.",
            "Enterprises are expanding governance and evaluation requirements for agentic systems.",
            "Human-in-the-loop review remains common for higher-risk support decisions.",
            "Operational value depends on knowledge quality and workflow integration.",
            "Teams increasingly measure agents on containment, accuracy, and escalation quality.",
        ],
        faiss_index_path="./faiss_indexes/test/index.faiss",
        total_chunks_stored=42,
        timestamp=datetime.now(timezone.utc),
    )


def _mock_outline_payload() -> dict[str, object]:
    sections = [
        {
            "section_number": 1,
            "title": "Introduction and Framing",
            "argument": "Define the topic and why it matters.",
            "key_points": [
                "Set the context for enterprise AI agents in support.",
                "Describe the operational problem space.",
                "Preview the report structure.",
            ],
            "suggested_sources": [
                "https://example.com/source-1",
                "https://example.com/source-2",
            ],
            "target_word_count": 220,
        },
        {
            "section_number": 2,
            "title": "Current Landscape",
            "argument": "Explain how enterprises are currently deploying support agents.",
            "key_points": [
                "Summarize adoption patterns.",
                "Explain where teams are seeing measurable value.",
                "Describe common implementation boundaries.",
            ],
            "suggested_sources": [
                "https://example.com/source-3",
                "https://example.com/source-4",
            ],
            "target_word_count": 320,
        },
        {
            "section_number": 3,
            "title": "Key Findings",
            "argument": "Synthesize the strongest research-backed findings.",
            "key_points": [
                "Highlight response-time improvements.",
                "Explain the role of governance.",
                "Describe evaluation metrics and escalation quality.",
            ],
            "suggested_sources": [
                "https://example.com/source-5",
                "https://example.com/source-6",
            ],
            "target_word_count": 360,
        },
        {
            "section_number": 4,
            "title": "Risks and Tradeoffs",
            "argument": "Assess the main operational and governance constraints.",
            "key_points": [
                "Cover hallucination and accuracy concerns.",
                "Explain workflow and data quality dependencies.",
                "Discuss human review requirements.",
            ],
            "suggested_sources": [
                "https://example.com/source-7",
                "https://example.com/source-8",
            ],
            "target_word_count": 300,
        },
        {
            "section_number": 5,
            "title": "Strategic Implications",
            "argument": "Translate the findings into operator-facing recommendations.",
            "key_points": [
                "Explain where to start adoption safely.",
                "Describe what teams should measure.",
                "Show how governance affects rollout decisions.",
            ],
            "suggested_sources": [
                "https://example.com/source-9",
                "https://example.com/source-10",
            ],
            "target_word_count": 320,
        },
    ]
    total_target_words = sum(
        section["target_word_count"] for section in sections
    )
    return {
        "topic": FAKE_TOPIC,
        "report_type": "analytical",
        "executive_summary": (
            "This report explains how enterprises are adopting AI agents in support "
            "operations and where the clearest value is emerging. It organizes the "
            "research into a structured plan the writer can execute section by section."
        ),
        "sections": sections,
        "total_target_words": total_target_words,
        "estimated_read_time_minutes": 8,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture(autouse=True)
def configure_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLANNER_USE_REAL_CREWAI", "false")


def test_successful_planning(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    valid_outline_json = ReportOutline.model_validate(_mock_outline_payload()).model_dump_json()

    monkeypatch.setattr(planner._CrewStub, "kickoff", lambda self, **kwargs: valid_outline_json)

    output = planner.run_planner(findings)

    assert isinstance(output, ReportOutline)
    assert 4 <= len(output.sections) <= 8
    assert output.total_target_words == sum(
        section.target_word_count for section in output.sections
    )


def test_section_titles_unique() -> None:
    payload = _mock_outline_payload()
    duplicate_title = payload["sections"][0]["title"]
    payload["sections"][1]["title"] = duplicate_title

    with pytest.raises(ValidationError, match="section titles must be unique"):
        ReportOutline.model_validate(payload)


def test_word_count_mismatch_raises() -> None:
    payload = _mock_outline_payload()
    payload["total_target_words"] = payload["total_target_words"] + 50

    with pytest.raises(
        ValidationError,
        match="total_target_words must equal the sum of all section target_word_count values",
    ):
        ReportOutline.model_validate(payload)


def test_planner_error_on_bad_output(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    monkeypatch.setattr(planner._CrewStub, "kickoff", lambda self, **kwargs: "{bad json")

    with pytest.raises(PlannerError, match="Planner pipeline failed"):
        planner.run_planner(findings)


def test_pipeline_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    outline = ReportOutline.model_validate(_mock_outline_payload())
    call_order = Mock()

    def fake_run_researcher(topic: str) -> FindingsOutput:
        call_order.researcher(topic)
        return findings

    def fake_run_planner(received_findings: FindingsOutput) -> ReportOutline:
        call_order.planner(received_findings.query)
        return outline

    monkeypatch.setattr(pipeline, "run_researcher", fake_run_researcher)
    monkeypatch.setattr(pipeline, "run_planner", fake_run_planner)

    result = pipeline.run_research_and_plan(FAKE_TOPIC)

    assert result == (findings, outline)
    assert call_order.mock_calls == [
        call.researcher(FAKE_TOPIC),
        call.planner(FAKE_TOPIC),
    ]
