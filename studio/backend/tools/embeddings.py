from __future__ import annotations

import asyncio
from threading import RLock

from langchain_core.embeddings import Embeddings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.tools.cache import EmbeddingCache

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:  # pragma: no cover - exercised via patched tests/fallback runtime
    OpenAIEmbeddings = None

try:
    from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

    OPENAI_RETRYABLE_EXCEPTIONS = (
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
    )
except ImportError:  # pragma: no cover - fallback when OpenAI SDK is unavailable
    OPENAI_RETRYABLE_EXCEPTIONS = (Exception,)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_RETRY_ATTEMPTS = 3
EMBEDDING_RETRY_DELAY_SECONDS = 5
EMBEDDING_COUNT_MISMATCH_ERROR = "Embedding response count did not match request count"
MISSING_OPENAI_API_KEY_ERROR = "OPENAI_API_KEY is required for embeddings"
MISSING_EMBEDDINGS_LIBRARY_ERROR = "langchain-openai is required for embeddings"

logger = get_logger(__name__)
_embeddings_lock = RLock()
_openai_embeddings: OpenAIEmbeddings | None = None
_cached_embeddings: Embeddings | None = None


class CachedEmbeddings(Embeddings):
    def __init__(self, underlying_embeddings: OpenAIEmbeddings):
        self.underlying_embeddings = underlying_embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)


def _get_openai_embeddings() -> OpenAIEmbeddings:
    global _openai_embeddings

    if not settings.openai_api_key:
        raise RuntimeError(MISSING_OPENAI_API_KEY_ERROR)
    if OpenAIEmbeddings is None:
        raise RuntimeError(MISSING_EMBEDDINGS_LIBRARY_ERROR)

    if _openai_embeddings is not None:
        return _openai_embeddings

    with _embeddings_lock:
        if _openai_embeddings is None:
            _openai_embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=EMBEDDING_MODEL,
            )

    return _openai_embeddings


def get_embeddings() -> Embeddings:
    global _cached_embeddings

    if _cached_embeddings is not None:
        return _cached_embeddings

    with _embeddings_lock:
        if _cached_embeddings is None:
            _cached_embeddings = CachedEmbeddings(_get_openai_embeddings())

    return _cached_embeddings


@retry(
    stop=stop_after_attempt(EMBEDDING_RETRY_ATTEMPTS),
    wait=wait_fixed(EMBEDDING_RETRY_DELAY_SECONDS),
    retry=retry_if_exception_type(OPENAI_RETRYABLE_EXCEPTIONS),
    reraise=True,
)
def _embed_uncached_texts(texts: list[str]) -> list[list[float]]:
    logger.debug("Embedding text_count=%s", len(texts))
    return _get_openai_embeddings().embed_documents(texts)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    cache = EmbeddingCache()
    cached_embeddings = cache.get_many(texts)
    uncached_texts = [
        text
        for text in dict.fromkeys(texts)
        if cached_embeddings.get(text) is None
    ]

    if uncached_texts:
        new_embeddings = _embed_uncached_texts(uncached_texts)
        if len(new_embeddings) != len(uncached_texts):
            raise RuntimeError(EMBEDDING_COUNT_MISMATCH_ERROR)

        new_embedding_map = dict(zip(uncached_texts, new_embeddings))
        cache.set_many(new_embedding_map)
        cached_embeddings.update(new_embedding_map)

    results: list[list[float]] = []
    for text in texts:
        embedding = cached_embeddings.get(text)
        if embedding is None:
            raise RuntimeError(EMBEDDING_COUNT_MISMATCH_ERROR)
        results.append(embedding)

    return results
