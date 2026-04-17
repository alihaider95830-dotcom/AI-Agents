from __future__ import annotations

import json
import inspect
import logging
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

try:
    import appdirs
except ImportError:  # pragma: no cover - depends on environment
    appdirs = None
from langchain_core.tools import StructuredTool

from exceptions import ResearcherError
from schemas.findings import FindingsOutput, SourceItem

logger = logging.getLogger(__name__)
CREWAI_LOCALAPPDATA_ENV_VAR = "RESEARCHER_CREWAI_LOCALAPPDATA"

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

MIN_RESEARCH_SOURCES = 8
MAX_RESEARCH_SOURCES = 12
DEFAULT_RESEARCH_MODEL = "gpt-4o-mini"
DEFAULT_MAX_SOURCES = 10
DEFAULT_CHUNK_SIZE = 500
DEFAULT_SIMILARITY_TOP_K = 15
DEFAULT_FAISS_PERSIST_DIR = "./faiss_indexes"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10
FAISS_INDEX_FILENAME = "index.faiss"
SOURCE_SNIPPET_LENGTH = 300
REAL_CREW_ENV_VAR = "RESEARCHER_USE_REAL_CREWAI"
FALLBACK_CHUNK_OVERLAP_DIVISOR = 10
FALLBACK_MIN_CHUNK_LENGTH = 50


@dataclass(slots=True)
class ResearcherConfig:
    """Runtime configuration for the Researcher agent."""

    model_name: str = field(
        default_factory=lambda: os.getenv("RESEARCHER_MODEL_NAME", DEFAULT_RESEARCH_MODEL)
    )
    max_sources: int = field(
        default_factory=lambda: int(os.getenv("RESEARCHER_MAX_SOURCES", DEFAULT_MAX_SOURCES))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("RESEARCHER_CHUNK_SIZE", DEFAULT_CHUNK_SIZE))
    )
    similarity_top_k: int = field(
        default_factory=lambda: int(
            os.getenv("RESEARCHER_SIMILARITY_TOP_K", DEFAULT_SIMILARITY_TOP_K)
        )
    )
    faiss_persist_dir: str = field(
        default_factory=lambda: os.getenv(
            "RESEARCHER_FAISS_PERSIST_DIR",
            DEFAULT_FAISS_PERSIST_DIR,
        )
    )
    request_timeout: int = field(
        default_factory=lambda: int(
            os.getenv("RESEARCHER_REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT_SECONDS)
        )
    )

    def __post_init__(self) -> None:
        """Validate config bounds after construction."""
        if not MIN_RESEARCH_SOURCES <= self.max_sources <= MAX_RESEARCH_SOURCES:
            raise ValueError(
                f"max_sources must be between {MIN_RESEARCH_SOURCES} and {MAX_RESEARCH_SOURCES}"
            )
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.similarity_top_k <= 0:
            raise ValueError("similarity_top_k must be positive")
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")


class _CrewAIStub:
    """Simple fallback used when CrewAI cannot be imported safely."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _AgentStub(_CrewAIStub):
    """Fallback agent container."""


class _TaskStub(_CrewAIStub):
    """Fallback task container."""


class _CrewStub(_CrewAIStub):
    """Fallback crew container."""

    def kickoff(self, *args: Any, **kwargs: Any) -> str:
        raise RuntimeError("CrewAI kickoff is unavailable in fallback mode")


def _using_real_crewai() -> bool:
    """Return True when the real CrewAI runtime is explicitly enabled."""
    return os.getenv(REAL_CREW_ENV_VAR, "false").lower() == "true"


@lru_cache(maxsize=1)
def _load_crewai_classes() -> tuple[type[Any], type[Any], type[Any]]:
    """Import CrewAI safely, or fall back to lightweight stubs."""
    if not _using_real_crewai():
        return _AgentStub, _TaskStub, _CrewStub

    try:
        from crewai import Agent, Crew, Task

        return Agent, Task, Crew
    except Exception as exc:  # pragma: no cover - exercised in constrained environments
        logger.warning("CrewAI import failed, using fallback stubs: %s", exc)
        return _AgentStub, _TaskStub, _CrewStub


def _fallback_search_web(query: str) -> list[dict[str, Any]]:
    """Use the existing backend search tool when agents.tools is unavailable."""
    try:
        from backend.tools.search import SearchTool
    except Exception as exc:
        raise RuntimeError("search_web is unavailable in this environment") from exc

    return SearchTool(max_results=MAX_RESEARCH_SOURCES).run(query)


def _fallback_scrape_url(url: str) -> str:
    """Use the existing backend scraper when agents.tools is unavailable."""
    try:
        from backend.tools.scraper import ScraperTool
    except Exception as exc:
        raise RuntimeError("scrape_url is unavailable in this environment") from exc

    scraper = ScraperTool()
    try:
        result = scraper.fetch(url)
    finally:
        scraper.close()
    if result is None:
        raise RuntimeError(f"Could not scrape content from {url}")
    return result


def _fallback_chunk_text(text: str, chunk_size: int) -> list[str]:
    """Chunk text locally when the milestone chunker module is unavailable."""
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return []

    overlap = max(1, chunk_size // FALLBACK_CHUNK_OVERLAP_DIVISOR)
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    text_length = len(cleaned_text)

    for start in range(0, text_length, step):
        chunk = cleaned_text[start : start + chunk_size].strip()
        if not chunk:
            continue
        if len(chunk) < min(FALLBACK_MIN_CHUNK_LENGTH, chunk_size) and chunks:
            break
        chunks.append(chunk)
        if start + chunk_size >= text_length:
            break

    return chunks


class _SimpleVectorStore:
    """Fallback vector store used when the milestone store module is unavailable."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def embed_and_store(self, chunks: list[str], metadata: list[dict[str, Any]]) -> None:
        """Store chunks and their metadata in memory."""
        for chunk, item_metadata in zip(chunks, metadata):
            self._entries.append({"chunk": chunk, "metadata": item_metadata})

    def similarity_search(self, query: str, k: int) -> list[str]:
        """Rank chunks by simple token overlap with the query."""
        query_terms = set(query.lower().split())
        ranked_entries = sorted(
            self._entries,
            key=lambda item: (
                -len(query_terms.intersection(item["chunk"].lower().split())),
                -len(item["chunk"]),
            ),
        )
        return [item["chunk"] for item in ranked_entries[:k] if item["chunk"].strip()]

    def persist(self, path: str) -> None:
        """Write the in-memory index to disk."""
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(self._entries), encoding="utf-8")

    def load(self, path: str) -> None:
        """Load the in-memory index from disk."""
        target_path = Path(path)
        if not target_path.exists():
            self._entries = []
            return
        self._entries = json.loads(target_path.read_text(encoding="utf-8"))


def _get_search_web() -> Callable[[str], list[dict[str, Any]]]:
    """Resolve the milestone search wrapper or fall back to backend tooling."""
    try:
        from agents.tools.search import search_web as search_callable

        return search_callable
    except ImportError:
        return _fallback_search_web


def _get_scrape_url() -> Callable[[str], str]:
    """Resolve the milestone scraper wrapper or fall back to backend tooling."""
    try:
        from agents.tools.scraper import scrape_url as scrape_callable

        return scrape_callable
    except ImportError:
        return _fallback_scrape_url


def _get_chunk_text() -> Callable[[str, int], list[str]]:
    """Resolve the milestone chunker wrapper or fall back to local chunking."""
    try:
        from agents.tools.chunker import chunk_text as chunk_callable

        return chunk_callable
    except ImportError:
        return _fallback_chunk_text


def _get_vector_store() -> Any:
    """Resolve the milestone FAISS store or fall back to a simple local store."""
    try:
        from agents.vector_store import VectorStore

        return VectorStore()
    except ImportError:
        return _SimpleVectorStore()


search_web = _get_search_web()
scrape_url = _get_scrape_url()
chunk_text = _get_chunk_text()


def _build_tool(function: Callable[..., Any], name: str, description: str) -> Any:
    """Wrap a callable as a LangChain/CrewAI-compatible tool."""
    if _using_real_crewai():
        from crewai.tools import tool as crewai_tool

        tool_function = function
        tool_signature = inspect.signature(function)
        if tool_function.__doc__ is None:
            def tool_function(*args: Any, **kwargs: Any) -> Any:
                """Fallback CrewAI tool wrapper."""
                return function(*args, **kwargs)

            tool_function.__name__ = name
            tool_function.__doc__ = description
            tool_function.__signature__ = tool_signature
            tool_function.__annotations__ = dict(getattr(function, "__annotations__", {}))

        return crewai_tool(name)(tool_function)

    return StructuredTool.from_function(
        func=function,
        name=name,
        description=description,
    )


def create_researcher_agent(config: ResearcherConfig) -> Any:
    """Create the CrewAI researcher agent definition."""
    Agent, _, _ = _load_crewai_classes()
    tools = [
        _build_tool(search_web, "search_web", "Search the web for research sources."),
        _build_tool(scrape_url, "scrape_url", "Scrape a single URL for readable text."),
    ]
    return Agent(
        role="Senior Research Analyst",
        goal="Thorough, multi-source research with fact extraction",
        backstory=(
            "A meticulous analyst who prioritizes source diversity, careful fact "
            "checking, and clean research handoffs for downstream planning."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        llm=config.model_name,
    )


def create_researcher_task(agent: Any) -> Any:
    """Create the CrewAI task definition for the researcher."""
    _, Task, _ = _load_crewai_classes()
    expected_output = json.dumps(FindingsOutput.model_json_schema(), indent=2)
    return Task(
        description=(
            "Research the topic `{topic}` by searching the web, scraping each source, "
            "chunking the content, storing embeddings in FAISS, and returning a strict "
            "JSON object that matches the FindingsOutput schema."
        ),
        expected_output=expected_output,
        agent=agent,
    )


def _normalize_sources(
    raw_sources: list[dict[str, Any]],
    max_sources: int,
) -> list[dict[str, str]]:
    """Deduplicate and normalize search results."""
    normalized_sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for item in raw_sources:
        url = str(item.get("url") or "").strip()
        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        normalized_sources.append(
            {
                "url": url,
                "title": str(item.get("title") or url).strip(),
                "snippet": str(item.get("snippet") or "").strip(),
            }
        )
        if len(normalized_sources) >= max_sources:
            break

    return normalized_sources


def _scrape_with_timeout(url: str, timeout: int) -> str:
    """Scrape a single URL with a hard timeout."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(scrape_url, url)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"Timed out scraping {url}") from exc


def _extract_key_facts(store: Any, topic: str, top_k: int) -> list[str]:
    """Run similarity search and deduplicate the returned facts."""
    raw_facts = store.similarity_search(topic, k=top_k)
    key_facts: list[str] = []
    seen_facts: set[str] = set()

    for item in raw_facts:
        fact = str(item).strip()
        if not fact or fact in seen_facts:
            continue
        seen_facts.add(fact)
        key_facts.append(fact)

    return key_facts


def _perform_research(topic: str, config: ResearcherConfig) -> FindingsOutput:
    """Execute the deterministic research pipeline and return structured findings."""
    raw_sources = search_web(topic)
    normalized_sources = _normalize_sources(raw_sources, config.max_sources)
    if len(normalized_sources) < MIN_RESEARCH_SOURCES:
        raise ResearcherError(
            f"Expected at least {MIN_RESEARCH_SOURCES} sources, found {len(normalized_sources)}"
        )

    store = _get_vector_store()
    source_items: list[SourceItem] = []
    all_chunks: list[str] = []
    all_metadata: list[dict[str, Any]] = []

    for item in normalized_sources:
        url = item["url"]
        title = item["title"]
        fallback_snippet = item["snippet"][:SOURCE_SNIPPET_LENGTH]
        try:
            scraped_text = _scrape_with_timeout(url, config.request_timeout)
            snippet = scraped_text[:SOURCE_SNIPPET_LENGTH]
            scrape_success = True
            chunks = chunk_text(scraped_text, config.chunk_size)
        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", url, exc)
            snippet = fallback_snippet
            scrape_success = False
            chunks = []

        source_items.append(
            SourceItem(
                url=url,
                title=title,
                snippet=snippet,
                scrape_success=scrape_success,
            )
        )

        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({"url": url, "title": title})

    if all_chunks:
        store.embed_and_store(all_chunks, all_metadata)

    job_id = uuid.uuid4().hex
    persist_dir = Path(config.faiss_persist_dir) / job_id
    persist_dir.mkdir(parents=True, exist_ok=True)
    faiss_index_path = persist_dir / FAISS_INDEX_FILENAME
    store.persist(str(faiss_index_path))
    key_facts = _extract_key_facts(store, topic, config.similarity_top_k)

    return FindingsOutput(
        query=topic,
        sources=source_items,
        key_facts=key_facts,
        faiss_index_path=str(faiss_index_path),
        total_chunks_stored=len(all_chunks),
        timestamp=datetime.now(timezone.utc),
    )


def _kickoff_research_crew(crew: Any, topic: str, config: ResearcherConfig) -> str:
    """Kick off the crew when enabled, otherwise run the deterministic pipeline."""
    if _using_real_crewai() and hasattr(crew, "kickoff"):
        raw_output = crew.kickoff(inputs={"topic": topic})
        if hasattr(raw_output, "raw"):
            return str(raw_output.raw)
        return str(raw_output)

    findings = _perform_research(topic, config)
    return findings.model_dump_json()


def run_researcher(topic: str) -> FindingsOutput:
    """Run the Researcher agent and return validated structured findings."""
    config = ResearcherConfig()
    Agent, Task, Crew = _load_crewai_classes()

    try:
        researcher_agent = create_researcher_agent(config)
        researcher_task = create_researcher_task(researcher_agent)
        crew = Crew(
            agents=[researcher_agent] if Agent is not _AgentStub else [researcher_agent],
            tasks=[researcher_task] if Task is not _TaskStub else [researcher_task],
            verbose=True,
        )
        raw_output = _kickoff_research_crew(crew, topic, config)
        return FindingsOutput.model_validate_json(raw_output)
    except ResearcherError:
        raise
    except Exception as exc:
        logger.exception("Researcher pipeline failed for topic=%s", topic)
        raise ResearcherError(f"Researcher pipeline failed for topic '{topic}': {exc}") from exc
