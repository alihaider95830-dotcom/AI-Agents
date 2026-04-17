from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agents import crew as crew_module
from agents import planner, qa, researcher, writer
from exceptions import PipelineError, QAError, ResearcherError
from schemas.draft import ReportDraft, count_words
from schemas.findings import FindingsOutput
from schemas.outline import ReportOutline
from schemas.report import FinalReport

FAKE_TOPIC = "The future of renewable energy"


def _findings_payload() -> dict[str, object]:
    return {
        "query": FAKE_TOPIC,
        "sources": [
            {
                "url": f"https://example.com/source-{index}",
                "title": f"Source {index}",
                "snippet": f"Snippet {index}",
                "scrape_success": True,
            }
            for index in range(1, 9)
        ],
        "key_facts": [
            (
                "Renewable energy deployment is accelerating because costs have "
                "continued to fall."
            ),
            (
                "Grid modernization and storage are becoming central to reliable "
                "renewable expansion."
            ),
            (
                "Public policy and permitting reforms still shape the pace of "
                "project delivery."
            ),
            (
                "Corporate procurement is increasing demand for clean power in "
                "multiple markets."
            ),
            (
                "Transmission bottlenecks remain a major constraint on "
                "large-scale deployment."
            ),
        ],
        "faiss_index_path": "./faiss_indexes/test/index.faiss",
        "total_chunks_stored": 48,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _outline_payload() -> dict[str, object]:
    sections = [
        {
            "section_number": 1,
            "title": "Introduction",
            "argument": "Explain why renewable energy is a defining strategic topic.",
            "key_points": [
                "Set the market context.",
                "Define the report scope.",
                "Preview the major drivers.",
            ],
            "suggested_sources": [
                "https://example.com/source-1",
                "https://example.com/source-2",
            ],
            "target_word_count": 120,
        },
        {
            "section_number": 2,
            "title": "Market Momentum",
            "argument": (
                "Show how cost curves and procurement demand are driving adoption."
            ),
            "key_points": [
                "Explain cost declines.",
                "Describe procurement demand.",
                "Connect adoption to deployment trends.",
            ],
            "suggested_sources": [
                "https://example.com/source-3",
                "https://example.com/source-4",
            ],
            "target_word_count": 140,
        },
        {
            "section_number": 3,
            "title": "Infrastructure Constraints",
            "argument": "Assess storage, transmission, and grid bottlenecks.",
            "key_points": [
                "Cover storage needs.",
                "Explain transmission constraints.",
                "Show how grid modernization affects rollout speed.",
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
            "argument": "Summarize the outlook and strategic implications.",
            "key_points": [
                "Reinforce the outlook.",
                "Show what needs to improve next.",
                "Close with a clear takeaway.",
            ],
            "suggested_sources": [
                "https://example.com/source-7",
                "https://example.com/source-8",
            ],
            "target_word_count": 110,
        },
    ]
    return {
        "topic": FAKE_TOPIC,
        "report_type": "analytical",
        "executive_summary": (
            "This report explains why renewable energy adoption is accelerating "
            "and what constraints still shape future deployment. It organizes "
            "the research into a practical narrative that moves from momentum "
            "to infrastructure implications."
        ),
        "sections": sections,
        "total_target_words": sum(section["target_word_count"] for section in sections),
        "estimated_read_time_minutes": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _section_payload(
    section_number: int,
    title: str,
    citation_numbers: list[int],
    citation_urls: list[str],
    citation_titles: list[str],
    target_word_count: int,
) -> dict[str, object]:
    lines = [
        (
            f"This section explains {title.lower()} and ties the discussion "
            f"back to renewable energy strategy [{citation_numbers[0]}]."
        ),
        f"- First point for {title.lower()} [{citation_numbers[0]}]",
        f"- Second point for {title.lower()} [{citation_numbers[-1]}]",
        (
            f"The cited evidence shows why {title.lower()} matters for "
            f"long-term planning and capital allocation [{citation_numbers[-1]}]."
        ),
    ]
    while len(" ".join(lines).split()) < target_word_count:
        lines.append(
            (
                f"Additional supporting detail clarifies the role of {title.lower()} "
                f"in the energy transition and the pace of adoption "
                f"[{citation_numbers[0]}]."
            )
        )

    content = "\n".join(lines)
    return {
        "section_number": section_number,
        "title": title,
        "content": content,
        "word_count": count_words(content),
        "citations": [
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
        ],
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
            "Market Momentum",
            [3, 4],
            ["https://example.com/source-3", "https://example.com/source-4"],
            ["Source 3", "Source 4"],
            140,
        ),
        _section_payload(
            3,
            "Infrastructure Constraints",
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
            "inline_reference": (
                f"[{index}] Source {index} - https://example.com/source-{index}"
            ),
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
            "This report explains why renewable energy adoption is accelerating "
            "and what constraints still shape future deployment."
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
            "This report explains why renewable energy adoption is accelerating "
            "and what constraints still shape future deployment."
        ),
        "sections": sections,
        "total_word_count": sum(section["word_count"] for section in sections),
        "all_citations": all_citations,
        "markdown_output": "\n".join(markdown_lines),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _final_report_payload(
    quality_score: float = 0.92,
    qa_flags: list[dict[str, object]] | None = None,
    qa_passed: bool = True,
) -> dict[str, object]:
    draft_payload = _draft_payload()
    return {
        "topic": FAKE_TOPIC,
        "report_type": "analytical",
        "executive_summary": draft_payload["executive_summary"],
        "markdown_output": draft_payload["markdown_output"],
        "total_word_count": draft_payload["total_word_count"],
        "all_citations": draft_payload["all_citations"],
        "qa_flags": qa_flags or [],
        "qa_passed": qa_passed,
        "quality_score": quality_score,
        "job_id": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _validated_findings() -> FindingsOutput:
    return FindingsOutput.model_validate(_findings_payload())


def _validated_outline() -> ReportOutline:
    return ReportOutline.model_validate(_outline_payload())


def _validated_draft() -> ReportDraft:
    outline = _validated_outline()
    return ReportDraft.model_validate(
        _draft_payload(),
        context={
            "section_targets": {
                section.section_number: section.target_word_count
                for section in outline.sections
            },
            "word_count_tolerance": 0.20,
        },
    )


@pytest.fixture(autouse=True)
def configure_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLANNER_USE_REAL_CREWAI", "false")
    monkeypatch.setenv("WRITER_USE_REAL_CREWAI", "false")
    monkeypatch.setenv("QA_USE_REAL_CREWAI", "false")
    monkeypatch.setenv("RESEARCHER_USE_REAL_CREWAI", "false")


def _mock_pipeline_outputs(
    monkeypatch: pytest.MonkeyPatch,
    quality_score: float = 0.92,
) -> None:
    findings = _validated_findings()
    outline = _validated_outline()
    draft = _validated_draft()
    final_report_json = FinalReport.model_validate(
        _final_report_payload(quality_score=quality_score)
    ).model_dump_json()

    monkeypatch.setattr(
        researcher,
        "_kickoff_research_crew",
        lambda crew_instance, topic, config: findings.model_dump_json(),
    )
    monkeypatch.setattr(
        planner._CrewStub,
        "kickoff",
        lambda self, **kwargs: outline.model_dump_json(),
    )
    monkeypatch.setattr(
        writer._CrewStub,
        "kickoff",
        lambda self, **kwargs: draft.model_dump_json(),
    )
    monkeypatch.setattr(
        qa._CrewStub,
        "kickoff",
        lambda self, **kwargs: final_report_json,
    )


def test_full_crew_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_pipeline_outputs(monkeypatch)

    output = crew_module.run_crew(FAKE_TOPIC)

    assert isinstance(output, FinalReport)
    assert output.qa_passed is True
    assert output.quality_score >= 0.75
    assert "## Introduction" in output.markdown_output


def test_qa_fails_on_low_score(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_pipeline_outputs(monkeypatch, quality_score=0.5)

    with pytest.raises(QAError, match="quality score below threshold"):
        qa.run_qa(_validated_draft(), _validated_findings())


def test_pipeline_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        crew_module,
        "run_researcher",
        lambda topic: (_ for _ in ()).throw(ResearcherError("research failure")),
    )

    with pytest.raises(PipelineError, match="Researcher step failed"):
        crew_module.run_crew(FAKE_TOPIC)


def test_qa_flags_unresolved_sets_qa_passed_false() -> None:
    report = FinalReport.model_validate(
        _final_report_payload(
            qa_flags=[
                {
                    "section_number": 1,
                    "issue_type": "factual",
                    "description": "Claim needs stronger support.",
                    "resolved": False,
                    "original_text": "Original statement",
                    "corrected_text": None,
                }
            ],
            qa_passed=True,
        )
    )

    assert report.qa_passed is False


def test_get_crew_status() -> None:
    status = crew_module.get_crew_status()

    assert status["researcher"] == "ready"
    assert status["planner"] == "ready"
    assert status["writer"] == "ready"
    assert status["qa"] == "ready"
    assert status["pipeline_version"] == "1.0.0"


def test_job_id_attached_to_report(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_pipeline_outputs(monkeypatch)

    report = crew_module.run_crew(FAKE_TOPIC, job_id="abc-123")

    assert report.job_id == "abc-123"
