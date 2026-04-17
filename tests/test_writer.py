from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock, call

import pytest
from pydantic import ValidationError

from agents import pipeline, writer
from exceptions import WriterError
from schemas.draft import ReportDraft, SectionDraft, count_words
from schemas.findings import FindingsOutput
from schemas.outline import ReportOutline

FAKE_TOPIC = "AI agents for enterprise knowledge operations"


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
            for index in range(1, 9)
        ],
        key_facts=[
            "Enterprises are using AI agents to reduce time spent searching fragmented knowledge bases.",
            "Reliable deployment depends on source quality, retrieval accuracy, and governance controls.",
            "Teams often begin with narrowly scoped workflows before expanding automation coverage.",
            "Citation-backed outputs improve trust and make review workflows easier to audit.",
            "Measurable value often appears in support, enablement, and internal operations use cases.",
        ],
        faiss_index_path="./faiss_indexes/test/index.faiss",
        total_chunks_stored=30,
        timestamp=datetime.now(timezone.utc),
    )


def _mock_outline() -> ReportOutline:
    sections = [
        {
            "section_number": 1,
            "title": "Introduction",
            "argument": "Explain why AI agents matter for enterprise knowledge work.",
            "key_points": [
                "Define the report scope.",
                "Explain the business context.",
                "Preview the major themes.",
            ],
            "suggested_sources": [
                "https://example.com/source-1",
                "https://example.com/source-2",
            ],
            "target_word_count": 120,
        },
        {
            "section_number": 2,
            "title": "Current Landscape",
            "argument": "Describe how enterprises are currently deploying these systems.",
            "key_points": [
                "Cover early adoption patterns.",
                "Show which workflows are being targeted first.",
                "Explain how teams are measuring value.",
            ],
            "suggested_sources": [
                "https://example.com/source-3",
                "https://example.com/source-4",
            ],
            "target_word_count": 140,
        },
        {
            "section_number": 3,
            "title": "Operational Considerations",
            "argument": "Assess governance, quality, and workflow requirements.",
            "key_points": [
                "Explain why data quality matters.",
                "Describe human review expectations.",
                "Show where citations improve trust.",
            ],
            "suggested_sources": [
                "https://example.com/source-5",
                "https://example.com/source-6",
            ],
            "target_word_count": 150,
        },
        {
            "section_number": 4,
            "title": "Conclusion",
            "argument": "Summarize the key takeaways and implications.",
            "key_points": [
                "Reinforce the core finding.",
                "Explain what strong implementation looks like.",
                "Close with a practical takeaway.",
            ],
            "suggested_sources": [
                "https://example.com/source-7",
                "https://example.com/source-8",
            ],
            "target_word_count": 110,
        },
    ]
    total_target_words = sum(section["target_word_count"] for section in sections)
    return ReportOutline.model_validate(
        {
            "topic": FAKE_TOPIC,
            "report_type": "analytical",
            "executive_summary": (
                "This report explains how enterprises are using AI agents to improve knowledge "
                "operations while balancing quality, trust, and governance. It organizes the "
                "topic into a practical narrative the writer can execute section by section."
            ),
            "sections": sections,
            "total_target_words": total_target_words,
            "estimated_read_time_minutes": 3,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def _section_payload(
    section_number: int,
    title: str,
    citation_numbers: list[int],
    citation_urls: list[str],
    citation_titles: list[str],
    target_word_count: int,
) -> dict[str, object]:
    body_lines = [
        (
            f"This section explains {title.lower()} in practical terms and keeps the discussion "
            f"grounded in the report topic [{citation_numbers[0]}]."
        ),
        f"- First key point for {title.lower()} [{citation_numbers[0]}]",
        f"- Second key point for {title.lower()} [{citation_numbers[-1]}]",
        (
            f"The evidence supports a careful but confident rollout strategy for {title.lower()} "
            f"across enterprise teams [{citation_numbers[-1]}]."
        ),
    ]
    while len(" ".join(body_lines).split()) < target_word_count:
        body_lines.append(
            f"Additional evidence clarifies how {title.lower()} connects to measurable outcomes "
            f"and operational trust [{citation_numbers[0]}]."
        )
    content = "\n".join(body_lines)

    citations = [
        {
            "index": index,
            "url": url,
            "title": citation_title,
            "inline_reference": f"[{index}] {citation_title} - {url}",
        }
        for index, url, citation_title in zip(
            citation_numbers,
            citation_urls,
            citation_titles,
        )
    ]
    return {
        "section_number": section_number,
        "title": title,
        "content": content,
        "word_count": count_words(content),
        "citations": citations,
        "within_word_target": True,
    }


def _draft_payload() -> dict[str, object]:
    sections = [
        _section_payload(
            1,
            "Introduction",
            [1, 2],
            ["https://example.com/source-1", "https://example.com/source-2"],
            ["Source 1", "Source 2"],
            120,
        ),
        _section_payload(
            2,
            "Current Landscape",
            [3, 4],
            ["https://example.com/source-3", "https://example.com/source-4"],
            ["Source 3", "Source 4"],
            140,
        ),
        _section_payload(
            3,
            "Operational Considerations",
            [5, 6],
            ["https://example.com/source-5", "https://example.com/source-6"],
            ["Source 5", "Source 6"],
            150,
        ),
        _section_payload(
            4,
            "Conclusion",
            [7, 8],
            ["https://example.com/source-7", "https://example.com/source-8"],
            ["Source 7", "Source 8"],
            110,
        ),
    ]
    all_citations = [
        {
            "index": index,
            "url": f"https://example.com/source-{index}",
            "title": f"Source {index}",
            "inline_reference": f"[{index}] Source {index} - https://example.com/source-{index}",
        }
        for index in range(1, 9)
    ]
    markdown_lines = [
        f"# {FAKE_TOPIC}",
        "**Type:** analytical",
        "**Estimated read time:** 3 min",
        "",
        "## Executive Summary",
        (
            "This report explains how enterprises are using AI agents to improve knowledge "
            "operations while balancing quality, trust, and governance."
        ),
        "",
    ]
    for section in sections:
        markdown_lines.extend([f"## {section['title']}", str(section["content"]), ""])
    markdown_lines.append("## References")
    markdown_lines.extend(citation["inline_reference"] for citation in all_citations)

    return {
        "topic": FAKE_TOPIC,
        "report_type": "analytical",
        "executive_summary": (
            "This report explains how enterprises are using AI agents to improve knowledge "
            "operations while balancing quality, trust, and governance."
        ),
        "sections": sections,
        "total_word_count": sum(section["word_count"] for section in sections),
        "all_citations": all_citations,
        "markdown_output": "\n".join(markdown_lines),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture(autouse=True)
def configure_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WRITER_USE_REAL_CREWAI", "false")


def test_successful_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    outline = _mock_outline()
    valid_draft_json = ReportDraft.model_validate(
        _draft_payload(),
        context={
            "section_targets": {
                section.section_number: section.target_word_count for section in outline.sections
            },
            "word_count_tolerance": 0.20,
        },
    ).model_dump_json()

    monkeypatch.setattr(writer._CrewStub, "kickoff", lambda self, **kwargs: valid_draft_json)

    output = writer.run_writer(outline, findings)

    assert isinstance(output, ReportDraft)
    assert len(output.sections) == 4
    for section in output.sections:
        assert f"## {section.title}" in output.markdown_output


def test_within_word_target_flag() -> None:
    within_content = " ".join(f"word{i}" for i in range(100)) + " [1]"
    within_section = SectionDraft.model_validate(
        {
            "section_number": 1,
            "title": "Within Range",
            "content": within_content,
            "word_count": count_words(within_content),
            "citations": [
                {
                    "index": 1,
                    "url": "https://example.com/source-1",
                    "title": "Source 1",
                    "inline_reference": "[1] Source 1 - https://example.com/source-1",
                }
            ],
            "within_word_target": True,
        },
        context={"target_word_count": 100, "word_count_tolerance": 0.20},
    )
    assert within_section.within_word_target is True

    outside_content = " ".join(f"word{i}" for i in range(130)) + " [1]"
    outside_section = SectionDraft.model_validate(
        {
            "section_number": 2,
            "title": "Outside Range",
            "content": outside_content,
            "word_count": count_words(outside_content),
            "citations": [
                {
                    "index": 1,
                    "url": "https://example.com/source-1",
                    "title": "Source 1",
                    "inline_reference": "[1] Source 1 - https://example.com/source-1",
                }
            ],
            "within_word_target": False,
        },
        context={"target_word_count": 100, "word_count_tolerance": 0.20},
    )
    assert outside_section.within_word_target is False


def test_duplicate_citations_raises() -> None:
    payload = _draft_payload()
    payload["all_citations"][1]["url"] = payload["all_citations"][0]["url"]
    payload["all_citations"][1]["inline_reference"] = payload["all_citations"][1][
        "inline_reference"
    ].replace(
        "https://example.com/source-2",
        "https://example.com/source-1",
    )

    with pytest.raises(ValidationError, match="all_citations must not contain duplicate URLs"):
        ReportDraft.model_validate(payload)


def test_assemble_markdown_structure() -> None:
    outline = _mock_outline()
    draft = ReportDraft.model_validate(
        _draft_payload(),
        context={
            "section_targets": {
                section.section_number: section.target_word_count for section in outline.sections
            },
            "word_count_tolerance": 0.20,
        },
    )

    markdown = writer.assemble_markdown(draft)

    assert markdown.startswith(f"# {FAKE_TOPIC}")
    assert "## References" in markdown
    for section in draft.sections:
        assert f"## {section.title}" in markdown


def test_writer_error_on_bad_output(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    outline = _mock_outline()
    monkeypatch.setattr(writer._CrewStub, "kickoff", lambda self, **kwargs: "{bad json")

    with pytest.raises(WriterError, match="Writer pipeline failed"):
        writer.run_writer(outline, findings)


def test_pipeline_three_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    findings = _mock_findings()
    outline = _mock_outline()
    draft = ReportDraft.model_validate(
        _draft_payload(),
        context={
            "section_targets": {
                section.section_number: section.target_word_count for section in outline.sections
            },
            "word_count_tolerance": 0.20,
        },
    )
    call_order = Mock()

    def fake_run_researcher(topic: str) -> FindingsOutput:
        call_order.researcher(topic)
        return findings

    def fake_run_planner(received_findings: FindingsOutput) -> ReportOutline:
        call_order.planner(received_findings.query)
        return outline

    def fake_run_writer(received_outline: ReportOutline, received_findings: FindingsOutput) -> ReportDraft:
        call_order.writer(received_outline.topic)
        assert received_findings == findings
        return draft

    monkeypatch.setattr(pipeline, "run_researcher", fake_run_researcher)
    monkeypatch.setattr(pipeline, "run_planner", fake_run_planner)
    monkeypatch.setattr(pipeline, "run_writer", fake_run_writer)

    result = pipeline.run_full_pipeline(FAKE_TOPIC)

    assert result == (findings, outline, draft)
    assert call_order.mock_calls == [
        call.researcher(FAKE_TOPIC),
        call.planner(FAKE_TOPIC),
        call.writer(FAKE_TOPIC),
    ]
