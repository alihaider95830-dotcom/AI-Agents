from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
import pytest
from tenacity import wait_fixed

from backend.tools import pipeline as pipeline_module
from backend.tools.chunker import MIN_CHUNK_TOKEN_COUNT, TextChunker
from backend.tools.extractor import DataExtractor
from backend.tools.scraper import ScraperTool, SCRAPER_REMOVABLE_TAGS
from backend.tools.search import SearchTool

SEARCH_QUERY_COUNT = 3
SEARCH_RESULTS_PER_QUERY = 2
SCRAPER_TEST_URL_COUNT = 4


def _mock_search_results() -> list[dict[str, str]]:
    return [
        {
            "title": "Result 1",
            "href": "https://example.com/article-1",
            "body": "Snippet one",
        },
        {
            "title": "Result 2",
            "href": "https://example.com/article-2",
            "body": "Snippet two",
        },
        {
            "title": "Result 3",
            "href": "https://example.com/article-3",
            "body": "Snippet three",
        },
    ]


def _mock_html(body: str) -> str:
    removable_sections = "".join(
        f"<{tag_name}>remove {tag_name}</{tag_name}>" for tag_name in SCRAPER_REMOVABLE_TAGS
    )
    return f"<html><body>{removable_sections}<main>{body}</main></body></html>"


def _tokens_to_text(chunker: TextChunker, token_count: int) -> str:
    seed_text = " ".join(f"token{i}" for i in range(token_count * 2))
    tokens = chunker.encoder.encode(seed_text)[:token_count]
    return chunker.encoder.decode(tokens)


def test_search_returns_structured_results() -> None:
    raw_results = _mock_search_results()
    with patch("backend.tools.search.DDGS") as ddgs_cls:
        ddgs_cls.return_value.text.return_value = raw_results

        results = SearchTool(max_results=len(raw_results)).run("on-device ai")

    assert len(results) == len(raw_results)
    assert set(results[0].keys()) == {"title", "url", "snippet", "source"}
    assert results[0]["source"] == "example.com"


def test_search_deduplicates_by_url() -> None:
    raw_results = _mock_search_results()
    raw_results.append(
        {
            "title": "Duplicate",
            "href": raw_results[0]["href"],
            "body": "Duplicate snippet",
        }
    )
    with patch("backend.tools.search.DDGS") as ddgs_cls:
        ddgs_cls.return_value.text.return_value = raw_results

        results = SearchTool().run("duplicate url test")

    assert len(results) == len(_mock_search_results())


def test_search_returns_empty_on_failure() -> None:
    with patch("backend.tools.search.DDGS") as ddgs_cls:
        ddgs_cls.side_effect = RuntimeError("duckduckgo unavailable")
        with patch.object(SearchTool._perform_search.retry, "wait", wait_fixed(0)):
            results = SearchTool().run("failing query")

    assert results == []


def test_search_multiple_merges_results() -> None:
    with patch("backend.tools.search.DDGS") as ddgs_cls:
        ddgs_cls.return_value.text.side_effect = [
            [
                {
                    "title": "A1",
                    "href": "https://example.com/a1",
                    "body": "A1 snippet",
                },
                {
                    "title": "A2",
                    "href": "https://example.com/a2",
                    "body": "A2 snippet",
                },
            ],
            [
                {
                    "title": "B1",
                    "href": "https://example.com/b1",
                    "body": "B1 snippet",
                },
                {
                    "title": "A2 duplicate",
                    "href": "https://example.com/a2",
                    "body": "Duplicate snippet",
                },
            ],
            [
                {
                    "title": "C1",
                    "href": "https://example.com/c1",
                    "body": "C1 snippet",
                },
                {
                    "title": "C2",
                    "href": "https://example.com/c2",
                    "body": "C2 snippet",
                },
            ],
        ]

        results = SearchTool(max_results=SEARCH_RESULTS_PER_QUERY).search_multiple(
            ["q1", "q2", "q3"]
        )

    assert len(results) == 5
    assert len({item["url"] for item in results}) == 5


def test_fetch_returns_clean_text() -> None:
    long_body = "Visible content " * 20
    response = Mock()
    response.text = _mock_html(long_body)
    response.raise_for_status = Mock()

    with patch("backend.tools.scraper.httpx.Client") as client_cls:
        client_cls.return_value.get.return_value = response
        scraper = ScraperTool()
        result = scraper.fetch("https://example.com/clean")
        scraper.close()

    assert result is not None
    assert "Visible content" in result
    assert "remove script" not in result
    assert "remove nav" not in result


def test_fetch_returns_none_on_short_content() -> None:
    response = Mock()
    response.text = _mock_html("short body")
    response.raise_for_status = Mock()

    with patch("backend.tools.scraper.httpx.Client") as client_cls:
        client_cls.return_value.get.return_value = response
        scraper = ScraperTool()
        result = scraper.fetch("https://example.com/short")
        scraper.close()

    assert result is None


def test_fetch_returns_none_on_http_error() -> None:
    request = httpx.Request("GET", "https://example.com/error")
    response = httpx.Response(500, request=request)

    with patch("backend.tools.scraper.httpx.Client") as client_cls:
        client_cls.return_value.get.side_effect = httpx.HTTPStatusError(
            "boom",
            request=request,
            response=response,
        )
        scraper = ScraperTool()
        result = scraper.fetch("https://example.com/error")
        scraper.close()

    assert result is None


def test_fetch_many_concurrent() -> None:
    def get_side_effect(url: str):
        response = Mock()
        response.text = _mock_html(f"Long content for {url} " * 20)
        response.raise_for_status = Mock()
        return response

    urls = [f"https://example.com/{index}" for index in range(SCRAPER_TEST_URL_COUNT)]
    with patch("backend.tools.scraper.httpx.Client") as client_cls:
        client_cls.return_value.get.side_effect = get_side_effect
        scraper = ScraperTool()
        results = scraper.fetch_many(urls, max_workers=SCRAPER_TEST_URL_COUNT)
        scraper.close()

    assert len(results) == SCRAPER_TEST_URL_COUNT
    assert set(results.keys()) == set(urls)


def test_chunk_long_text() -> None:
    chunker = TextChunker()
    text = _tokens_to_text(chunker, 2000)

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    first_tokens = chunker.encoder.encode(chunks[0]["text"])
    second_tokens = chunker.encoder.encode(chunks[1]["text"])
    assert first_tokens[-chunker.CHUNK_OVERLAP :] == second_tokens[: chunker.CHUNK_OVERLAP]


def test_chunk_short_text() -> None:
    chunker = TextChunker()
    text = _tokens_to_text(chunker, 100)

    chunks = chunker.chunk(text)

    assert len(chunks) == 1
    assert chunks[0]["total_chunks"] == 1


def test_chunk_empty_text() -> None:
    chunker = TextChunker()

    assert chunker.chunk("") == []


def test_chunk_metadata_preserved() -> None:
    chunker = TextChunker()
    text = _tokens_to_text(chunker, 600)
    metadata = {"url": "https://example.com", "title": "Example", "source": "example.com"}

    chunks = chunker.chunk(text, metadata=metadata)

    assert chunks
    assert all(item["metadata"] == metadata for item in chunks)


def test_chunk_discards_tiny_chunks() -> None:
    chunker = TextChunker()
    text = _tokens_to_text(chunker, 910)

    chunks = chunker.chunk(text)

    assert chunks
    assert all(item["token_count"] >= MIN_CHUNK_TOKEN_COUNT for item in chunks)


def test_extract_key_facts_returns_relevant_sentences() -> None:
    extractor = DataExtractor()
    text = (
        "On-device AI shipments reached 120 million units in 2024 across consumer devices. "
        "This sentence is unrelated and should not pass the filter. "
        "On-device AI reduced latency by 43% for mobile assistants in 2025 benchmarks. "
        "Another unrelated sentence without numbers. "
        "Enterprise on-device AI budgets hit $2.4B as deployments expanded globally in 2024. "
        "Noise sentence one. Noise sentence two. Noise sentence three. Noise sentence four. "
        "Noise sentence five."
    )

    results = extractor.extract_key_facts(text, "on-device AI")

    assert len(results) == 3


def test_extract_statistics_finds_percentages() -> None:
    extractor = DataExtractor()
    text = "Revenue grew by 43% year over year as the market expanded."

    results = extractor.extract_statistics(text)

    assert any("43%" in item for item in results)


def test_extract_statistics_finds_dollar_amounts() -> None:
    extractor = DataExtractor()
    text = "Analysts estimate a $2.4B market for on-device AI chips by 2025."

    results = extractor.extract_statistics(text)

    assert any("$2.4B" in item for item in results)


def test_extract_competitor_mentions_counts_correctly() -> None:
    extractor = DataExtractor()
    text = "OpenAI leads. Google follows. OpenAI expands. OPENAI partners widely."

    results = extractor.extract_competitor_mentions(text, ["OpenAI", "Google"])

    assert results == {"OpenAI": 3, "Google": 1}


def test_extract_competitor_mentions_excludes_zero_count() -> None:
    extractor = DataExtractor()
    text = "OpenAI is mentioned once here."

    results = extractor.extract_competitor_mentions(text, ["OpenAI", "Google"])

    assert "Google" not in results


def test_research_topic_end_to_end() -> None:
    search_tool = Mock()
    scraper = Mock()
    chunker = Mock()
    vector_store = Mock()
    extractor = Mock()

    search_tool.search_multiple.return_value = [
        {
            "title": "Source 1",
            "url": "https://example.com/source-1",
            "source": "example.com",
            "snippet": "Snippet 1",
        }
    ]
    scraper.fetch_many.return_value = {
        "https://example.com/source-1": "Long scraped content with 43% growth."
    }
    chunker.chunk_documents.return_value = [
        {"text": "chunk", "metadata": {"url": "https://example.com/source-1"}}
    ]
    extractor.extract_key_facts.return_value = ["Fact 1"]
    extractor.extract_statistics.return_value = ["43% growth"]

    with patch.object(pipeline_module, "SearchTool", return_value=search_tool), patch.object(
        pipeline_module, "ScraperTool", return_value=scraper
    ), patch.object(pipeline_module, "TextChunker", return_value=chunker), patch.object(
        pipeline_module.store_manager, "get", return_value=vector_store
    ), patch.object(pipeline_module, "DataExtractor", return_value=extractor):
        result = pipeline_module.research_topic(
            "on-device AI",
            "market_analysis",
            "job-123",
        )

    assert {
        "topic",
        "report_type",
        "sources",
        "documents_scraped",
        "chunks_indexed",
        "key_facts",
        "statistics",
        "vector_store_index",
        "summary",
    }.issubset(result.keys())
    vector_store.add_chunks.assert_called_once()
    scraper.close.assert_called_once()


def test_research_topic_closes_scraper_on_error() -> None:
    search_tool = Mock()
    scraper = Mock()
    chunker = Mock()
    vector_store = Mock()
    extractor = Mock()

    search_tool.search_multiple.side_effect = RuntimeError("search failed")

    with patch.object(pipeline_module, "SearchTool", return_value=search_tool), patch.object(
        pipeline_module, "ScraperTool", return_value=scraper
    ), patch.object(pipeline_module, "TextChunker", return_value=chunker), patch.object(
        pipeline_module.store_manager, "get", return_value=vector_store
    ), patch.object(pipeline_module, "DataExtractor", return_value=extractor):
        with pytest.raises(RuntimeError, match="search failed"):
            pipeline_module.research_topic("on-device AI", "market_analysis", "job-123")

    scraper.close.assert_called_once()
