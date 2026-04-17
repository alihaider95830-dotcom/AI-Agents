from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agents import researcher
from schemas.findings import FindingsOutput

FAKE_TOPIC = "AI-native B2B SaaS market"
SUCCESSFUL_SOURCE_COUNT = 10
FAILED_SCRAPE_COUNT = 3
MIN_EXPECTED_SOURCES = 8


def _fake_sources(count: int) -> list[dict[str, str]]:
    return [
        {
            "url": f"https://example.com/article-{index}",
            "title": f"Article {index}",
            "snippet": f"Snippet {index}",
        }
        for index in range(count)
    ]


def _fake_scrape_content(url: str) -> str:
    return (
        f"Research content from {url}. "
        f"This article contains facts about {FAKE_TOPIC}. "
        "Revenue grew 42 percent year over year across the category. "
        "Enterprise adoption accelerated in 2025 with strong demand signals. "
        * 8
    )


@pytest.fixture(autouse=True)
def configure_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RESEARCHER_FAISS_PERSIST_DIR", str(tmp_path / "faiss_indexes"))
    monkeypatch.setenv("RESEARCHER_USE_REAL_CREWAI", "false")


def test_successful_research(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(researcher, "search_web", lambda query: _fake_sources(SUCCESSFUL_SOURCE_COUNT))
    monkeypatch.setattr(researcher, "scrape_url", _fake_scrape_content)

    output = researcher.run_researcher(FAKE_TOPIC)

    assert isinstance(output, FindingsOutput)
    assert len(output.sources) >= MIN_EXPECTED_SOURCES
    assert output.key_facts
    assert Path(output.faiss_index_path).exists()


def test_failed_scrape_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    failed_urls = {
        f"https://example.com/article-{index}"
        for index in range(FAILED_SCRAPE_COUNT)
    }

    def scrape_with_failures(url: str) -> str:
        if url in failed_urls:
            raise RuntimeError("scrape failed")
        return _fake_scrape_content(url)

    monkeypatch.setattr(researcher, "search_web", lambda query: _fake_sources(SUCCESSFUL_SOURCE_COUNT))
    monkeypatch.setattr(researcher, "scrape_url", scrape_with_failures)

    output = researcher.run_researcher(FAKE_TOPIC)

    failed_sources = [item for item in output.sources if not item.scrape_success]
    assert len(failed_sources) == FAILED_SCRAPE_COUNT
    assert len(output.sources) >= MIN_EXPECTED_SOURCES


def test_insufficient_sources_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(researcher, "search_web", lambda query: _fake_sources(5))

    with pytest.raises(researcher.ResearcherError, match="Expected at least 8 sources"):
        researcher.run_researcher(FAKE_TOPIC)


def test_findings_schema_validation() -> None:
    with pytest.raises(ValidationError):
        FindingsOutput(
            query=FAKE_TOPIC,
            sources=[
                {
                    "url": "ftp://invalid-url",
                    "title": "Bad Source",
                    "snippet": "bad",
                    "scrape_success": True,
                }
            ],
            key_facts=["Fact 1"],
            faiss_index_path="",
            total_chunks_stored=1,
            timestamp="not-a-datetime",
        )


def test_faiss_index_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(researcher, "search_web", lambda query: _fake_sources(SUCCESSFUL_SOURCE_COUNT))
    monkeypatch.setattr(researcher, "scrape_url", _fake_scrape_content)

    output = researcher.run_researcher(FAKE_TOPIC)

    assert Path(output.faiss_index_path).exists()
