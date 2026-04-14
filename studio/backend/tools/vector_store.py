from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from pydantic import ConfigDict, Field

from backend.core.config import settings
from backend.core.logging import get_logger

try:
    from langchain_community.vectorstores import FAISS
except ImportError:  # pragma: no cover - exercised via patched tests/fallback runtime
    FAISS = None

try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:  # pragma: no cover - exercised via patched tests/fallback runtime
    OpenAIEmbeddings = None

VECTOR_STORE_DEFAULT_INDEX_NAME = "default"
VECTOR_STORE_EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_STORE_SEARCH_K = 5
VECTOR_STORE_SEARCH_MANY_MULTIPLIER = 2


class VectorStore:
    def __init__(self, index_name: str = VECTOR_STORE_DEFAULT_INDEX_NAME):
        self.index_path = Path(settings.vector_store_path) / index_name
        self.logger = get_logger(__name__)
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for VectorStore")
        if OpenAIEmbeddings is None:
            raise RuntimeError("langchain-openai is required for VectorStore")
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=VECTOR_STORE_EMBEDDING_MODEL,
        )
        self.index: Any | None = None

    def load_or_create(self) -> None:
        if FAISS is None:
            raise RuntimeError("langchain-community is required for VectorStore")

        if self.index_path.exists() and any(self.index_path.iterdir()):
            self.index = FAISS.load_local(
                str(self.index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.logger.info("Loaded existing FAISS index from %s", self.index_path)
            return

        self.index = None
        self.logger.info("No existing index found, will create on first add")

    def add_chunks(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        if FAISS is None:
            raise RuntimeError("langchain-community is required for VectorStore")

        documents = [
            Document(
                page_content=chunk["text"],
                metadata=chunk.get("metadata") or {},
            )
            for chunk in chunks
        ]
        self.index_path.mkdir(parents=True, exist_ok=True)
        if self.index is None:
            self.index = FAISS.from_documents(documents, self.embeddings)
        else:
            self.index.add_documents(documents)
        self.index.save_local(str(self.index_path))
        self.logger.info(
            "Added %s chunks. Index saved to %s",
            len(chunks),
            self.index_path,
        )
        return len(chunks)

    def search(self, query: str, k: int = VECTOR_STORE_SEARCH_K) -> list[dict[str, Any]]:
        if self.index is None:
            return []

        raw_results = self.index.similarity_search_with_score(query, k=k)
        results = [
            {
                "text": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata,
            }
            for doc, score in raw_results
        ]
        return sorted(results, key=lambda item: item["score"])

    def search_many(self, queries: list[str], k: int = VECTOR_STORE_SEARCH_K) -> list[dict[str, Any]]:
        if not queries:
            return []

        merged_results: list[dict[str, Any]] = []
        seen_texts: set[str] = set()
        for query in queries:
            for item in self.search(query, k=k):
                text = item["text"]
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                merged_results.append(item)

        merged_results.sort(key=lambda item: item["score"])
        return merged_results[: k * VECTOR_STORE_SEARCH_MANY_MULTIPLIER]

    def clear(self) -> None:
        self.index = None
        if self.index_path.exists():
            shutil.rmtree(self.index_path)
        self.logger.info("Index cleared")


class VectorStoreToolLC(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "search_knowledge_base"
    description: str = (
        "Search the internal knowledge base of previously researched content. "
        "Input: a search query string."
    )
    store: Any = Field(exclude=True)

    def __init__(self, store: VectorStore, **kwargs: Any):
        super().__init__(store=store, **kwargs)

    def _run(self, query: str) -> str:
        results = self.store.search(query, k=VECTOR_STORE_SEARCH_K)
        if not results:
            return "No relevant content found in knowledge base."

        lines = []
        for index, item in enumerate(results):
            metadata = item.get("metadata") or {}
            lines.append(
                f"Result {index + 1} (relevance score: {item['score']:.3f})\n"
                f"{item['text']}\n"
                f"Source: {metadata.get('url', 'unknown')}\n"
            )
        return "\n".join(lines)

    def _arun(self, query: str):
        raise NotImplementedError
