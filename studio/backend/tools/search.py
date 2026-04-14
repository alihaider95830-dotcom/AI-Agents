from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from langchain_core.tools import BaseTool
from tenacity import retry, stop_after_attempt, wait_fixed

from backend.core.logging import get_logger

try:
    from duckduckgo_search import DDGS
except ImportError:  # pragma: no cover - exercised via patched tests/fallback runtime
    DDGS = None

DEFAULT_SEARCH_MAX_RESULTS = 10
SEARCH_RETRY_ATTEMPTS = 3
SEARCH_RETRY_DELAY_SECONDS = 2
SEARCH_MULTI_MAX_RESULTS_CAP = 50
SEARCH_EMPTY_MESSAGE = "No results found for this query."


def _extract_source(url: str) -> str:
    parsed = urlparse(url)
    source = parsed.netloc.lower() or parsed.path.lower()
    if source.startswith("www."):
        return source[4:]
    return source


class SearchTool:
    def __init__(self, max_results: int = DEFAULT_SEARCH_MAX_RESULTS):
        self.max_results = max_results
        self.logger = get_logger(__name__)

    @retry(
        stop=stop_after_attempt(SEARCH_RETRY_ATTEMPTS),
        wait=wait_fixed(SEARCH_RETRY_DELAY_SECONDS),
        reraise=True,
    )
    def _perform_search(self, query: str) -> list[dict[str, Any]]:
        if DDGS is None:
            raise RuntimeError("duckduckgo-search is not installed")

        ddgs = DDGS()
        return list(ddgs.text(query, max_results=self.max_results))

    def run(self, query: str) -> list[dict[str, str]]:
        try:
            raw_results = self._perform_search(query)
        except Exception as exc:
            self.logger.error("search failed for query=%s error=%s", query, exc)
            return []

        results: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for item in raw_results:
            url = str(item.get("href") or item.get("url") or "").strip()
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            results.append(
                {
                    "title": str(item.get("title") or "").strip(),
                    "url": url,
                    "snippet": str(item.get("body") or item.get("snippet") or "").strip(),
                    "source": _extract_source(url),
                }
            )

        self.logger.debug("search query=%s results=%s", query, len(results))
        return results

    def search_multiple(self, queries: list[str]) -> list[dict[str, str]]:
        if not queries:
            return []

        limit = min(self.max_results * len(queries), SEARCH_MULTI_MAX_RESULTS_CAP)
        merged_results: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for query in queries:
            for item in self.run(query):
                url = item["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                merged_results.append(item)
                if len(merged_results) >= limit:
                    return merged_results

        return merged_results[:limit]


class SearchToolLC(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for current information on a topic. Input: a search query string."
    )

    def _run(self, query: str) -> str:
        results = SearchTool().run(query)
        if not results:
            return SEARCH_EMPTY_MESSAGE

        lines = []
        for index, item in enumerate(results, start=1):
            lines.append(
                f"{index}. {item['title']} ({item['source']})\n"
                f"   {item['snippet']}\n"
                f"   URL: {item['url']}\n"
            )
        return "\n".join(lines)

    def _arun(self, query: str):
        raise NotImplementedError("Use _run — search is synchronous")
