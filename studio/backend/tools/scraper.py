from __future__ import annotations

import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from langchain_core.tools import BaseTool

from backend.core.logging import get_logger

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised via fallback runtime
    BeautifulSoup = None

SCRAPER_TIMEOUT_SECONDS = 15
SCRAPER_USER_AGENT = "Mozilla/5.0 (compatible; StudioBot/1.0)"
SCRAPER_DEFAULT_MAX_WORKERS = 4
SCRAPER_MIN_CONTENT_CHARACTERS = 100
SCRAPER_TRUNCATE_CHARACTERS = 3000
SCRAPER_TRUNCATED_SUFFIX = "... [truncated]"
SCRAPER_WHITESPACE_PATTERN = re.compile(r"\s+")
SCRAPER_REMOVABLE_TAGS = (
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "iframe",
    "noscript",
)


def _collapse_whitespace(text: str) -> str:
    return SCRAPER_WHITESPACE_PATTERN.sub(" ", text).strip()


def _basic_html_to_text(content: str) -> str:
    cleaned = content
    for tag_name in SCRAPER_REMOVABLE_TAGS:
        cleaned = re.sub(
            rf"<{tag_name}\b[^>]*>.*?</{tag_name}>",
            " ",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return _collapse_whitespace(html.unescape(cleaned))


class ScraperTool:
    def __init__(self):
        self.client = httpx.Client(
            timeout=SCRAPER_TIMEOUT_SECONDS,
            headers={"User-Agent": SCRAPER_USER_AGENT},
            follow_redirects=True,
        )
        self.logger = get_logger(__name__)

    def fetch(self, url: str) -> str | None:
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            self.logger.warning("scrape failed for url=%s error=%s", url, exc)
            return None

        if BeautifulSoup is None:
            cleaned_text = _basic_html_to_text(response.text)
        else:
            soup = BeautifulSoup(response.text, "html.parser")
            for tag_name in SCRAPER_REMOVABLE_TAGS:
                for element in soup.find_all(tag_name):
                    element.decompose()
            cleaned_text = _collapse_whitespace(
                soup.get_text(separator=" ", strip=True)
            )

        if len(cleaned_text) < SCRAPER_MIN_CONTENT_CHARACTERS:
            return None

        return cleaned_text

    def fetch_many(
        self,
        urls: list[str],
        max_workers: int = SCRAPER_DEFAULT_MAX_WORKERS,
    ) -> dict[str, str]:
        if not urls:
            return {}

        results: dict[str, str] = {}
        worker_count = max(1, max_workers)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {executor.submit(self.fetch, url): url for url in urls}
            for future in as_completed(future_map):
                url = future_map[future]
                try:
                    content = future.result()
                except Exception as exc:  # pragma: no cover - defensive logging path
                    self.logger.warning("scrape worker failed for url=%s error=%s", url, exc)
                    continue
                if content is not None:
                    results[url] = content

        return results

    def close(self):
        self.client.close()


class ScraperToolLC(BaseTool):
    name: str = "scrape_webpage"
    description: str = (
        "Fetch and extract the readable text content from a URL. Input: a valid URL string."
    )

    def _run(self, url: str) -> str:
        scraper = ScraperTool()
        try:
            result = scraper.fetch(url)
        finally:
            scraper.close()

        if result is None:
            return f"Could not extract content from {url}."
        if len(result) > SCRAPER_TRUNCATE_CHARACTERS:
            return f"{result[:SCRAPER_TRUNCATE_CHARACTERS]}{SCRAPER_TRUNCATED_SUFFIX}"
        return result

    def _arun(self, url: str):
        raise NotImplementedError
