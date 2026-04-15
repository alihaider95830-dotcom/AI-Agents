from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from pydantic import ConfigDict, Field

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.tools.embeddings import get_embeddings

try:
    from langchain_community.vectorstores import FAISS
except ImportError:  # pragma: no cover - exercised via patched tests/fallback runtime
    FAISS = None

VECTOR_STORE_DEFAULT_INDEX_NAME = "default"
VECTOR_STORE_SEARCH_K = 5
VECTOR_STORE_SEARCH_MANY_MULTIPLIER = 2
VECTOR_STORE_INDEX_FILE_GLOB = "*"
VECTOR_STORE_DISK_RELOAD_MESSAGE = "Detected index change on disk for %s; reloading"


class VectorStore:
    def __init__(self, index_name: str = VECTOR_STORE_DEFAULT_INDEX_NAME):
        self.index_name = index_name
        self.index_path = Path(settings.vector_store_path) / index_name
        self.logger = get_logger(__name__)
        self.embeddings = get_embeddings()
        self.index: Any | None = None
        self._loaded_signature: tuple[tuple[str, int, int], ...] | None = None

    def _has_index_files(self, path: Path | None = None) -> bool:
        target_path = path or self.index_path
        return target_path.exists() and any(target_path.iterdir())

    def _index_signature(
        self,
        path: Path | None = None,
    ) -> tuple[tuple[str, int, int], ...] | None:
        target_path = path or self.index_path
        if not self._has_index_files(target_path):
            return None

        return tuple(
            sorted(
                (
                    str(file_path.relative_to(target_path)),
                    int(file_path.stat().st_size),
                    int(file_path.stat().st_mtime_ns),
                )
                for file_path in target_path.rglob(VECTOR_STORE_INDEX_FILE_GLOB)
                if file_path.is_file()
            )
        )

    def _remember_disk_state(self) -> None:
        self._loaded_signature = self._index_signature()

    def _index_size_bytes(self) -> int | None:
        if not self._has_index_files():
            return None

        return sum(
            file_path.stat().st_size
            for file_path in self.index_path.rglob(VECTOR_STORE_INDEX_FILE_GLOB)
            if file_path.is_file()
        )

    def _vector_count(self) -> int:
        if self.index is None:
            raise ValueError("Index is not loaded")
        return int(self.index.index.ntotal)

    def load_or_create(self) -> None:
        if FAISS is None:
            raise RuntimeError("langchain-community is required for VectorStore")

        if self._has_index_files():
            self.index = FAISS.load_local(
                str(self.index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self._remember_disk_state()
            self.logger.info("Loaded existing FAISS index from %s", self.index_path)
            return

        self.index = None
        self._loaded_signature = None
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
        self._remember_disk_state()
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

    def refresh_if_stale(self) -> bool:
        current_signature = self._index_signature()
        if current_signature == self._loaded_signature:
            return False

        self.logger.info(VECTOR_STORE_DISK_RELOAD_MESSAGE, self.index_name)
        self.load_or_create()
        return True

    def health_check(self) -> dict[str, Any]:
        try:
            return {
                "index_name": self.index_name,
                "loaded": self.index is not None,
                "index_path": str(self.index_path),
                "index_exists_on_disk": self._has_index_files(),
                "vector_count": self._vector_count() if self.index is not None else None,
                "index_size_bytes": self._index_size_bytes(),
            }
        except Exception as exc:  # pragma: no cover - exercised via tests with broken index objects
            return {"loaded": False, "error": str(exc)}

    def merge(self, other_index_name: str) -> int:
        if self.index is None:
            raise ValueError("Current index is not loaded")

        other_store = VectorStore(other_index_name)
        other_store.load_or_create()
        if other_store.index is None:
            raise ValueError("Other index is not loaded")

        self.index.merge_from(other_store.index)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.index.save_local(str(self.index_path))
        self._remember_disk_state()

        vector_count = self._vector_count()
        self.logger.info(
            "Merged index %s into %s. Total vectors: %s",
            other_index_name,
            self.index_path,
            vector_count,
        )
        return vector_count

    def get_all_metadata(self) -> list[dict[str, Any]]:
        if self.index is None:
            return []

        return [
            dict(getattr(document, "metadata", {}) or {})
            for document in self.index.docstore._dict.values()
        ]

    def list_sources(self) -> list[str]:
        return sorted(
            {
                str(metadata["url"])
                for metadata in self.get_all_metadata()
                if metadata.get("url")
            }
        )

    def clear(self) -> None:
        self.index = None
        self._loaded_signature = None
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
