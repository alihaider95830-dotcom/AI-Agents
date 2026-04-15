from __future__ import annotations

from backend.core.logging import get_logger
from backend.tools.chunker import TextChunker
from backend.tools.extractor import DataExtractor
from backend.tools.scraper import ScraperTool
from backend.tools.search import SearchTool
from backend.tools.store_manager import store_manager

logger = get_logger(__name__)

DEFAULT_MAX_SOURCES = 12
MARKET_ANALYSIS_SUFFIX = "market analysis 2024 2025"
STATISTICS_TRENDS_SUFFIX = "statistics trends competitors"
COMPETITOR_OVERVIEW_SUFFIX = "competitors comparison"
TREND_REPORT_SUFFIX = "emerging trends forecast"
COMPETITOR_OVERVIEW_REPORT_TYPE = "competitor_overview"
TREND_REPORT_REPORT_TYPE = "trend_report"


def research_topic(
    topic: str,
    report_type: str,
    job_id: str,
    max_sources: int = DEFAULT_MAX_SOURCES,
) -> dict:
    search_tool = SearchTool()
    scraper = ScraperTool()
    chunker = TextChunker()
    extractor = DataExtractor()
    vector_store = store_manager.get(job_id, auto_load=True)

    try:
        queries = [
            topic,
            f"{topic} {MARKET_ANALYSIS_SUFFIX}",
            f"{topic} {STATISTICS_TRENDS_SUFFIX}",
        ]
        if report_type == COMPETITOR_OVERVIEW_REPORT_TYPE:
            queries.append(f"{topic} {COMPETITOR_OVERVIEW_SUFFIX}")
        if report_type == TREND_REPORT_REPORT_TYPE:
            queries.append(f"{topic} {TREND_REPORT_SUFFIX}")

        search_results = search_tool.search_multiple(queries)[:max_sources]
        logger.info("Found %s sources for topic: %s", len(search_results), topic)

        scraped_by_url = scraper.fetch_many([item["url"] for item in search_results])

        documents: list[dict[str, str]] = []
        for item in search_results:
            url = item["url"]
            text = scraped_by_url.get(url)
            if text is None:
                continue
            documents.append(
                {
                    "title": item["title"],
                    "url": url,
                    "source": item["source"],
                    "snippet": item["snippet"],
                    "text": text,
                }
            )

        chunks = chunker.chunk_documents(documents)
        vector_store.add_chunks(chunks)

        all_text_combined = "\n\n".join(document["text"] for document in documents)
        key_facts = extractor.extract_key_facts(all_text_combined, topic)
        statistics = extractor.extract_statistics(all_text_combined)

        return {
            "topic": topic,
            "report_type": report_type,
            "sources": [
                {
                    "title": item["title"],
                    "url": item["url"],
                    "source": item["source"],
                    "snippet": item["snippet"],
                }
                for item in search_results
            ],
            "documents_scraped": len(documents),
            "chunks_indexed": len(chunks),
            "key_facts": key_facts,
            "statistics": statistics,
            "vector_store_index": job_id,
            "summary": (
                f"Researched {len(documents)} sources covering {topic}. "
                f"Indexed {len(chunks)} content chunks. "
                f"Extracted {len(key_facts)} key facts and {len(statistics)} statistics."
            ),
        }
    finally:
        scraper.close()
