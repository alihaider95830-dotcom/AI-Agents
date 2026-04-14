from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.logging import get_logger

try:
    import tiktoken
except ImportError:  # pragma: no cover - exercised via fallback runtime
    tiktoken = None

MIN_CHUNK_TOKEN_COUNT = 20


@dataclass
class SimpleTokenEncoder:
    def encode(self, text: str) -> list[str]:
        return text.split()

    def decode(self, tokens: list[str]) -> str:
        return " ".join(tokens)


class TextChunker:
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    ENCODING = "cl100k_base"

    def __init__(self):
        if tiktoken is None:
            self.encoder = SimpleTokenEncoder()
        else:
            self.encoder = tiktoken.get_encoding(self.ENCODING)
        self.logger = get_logger(__name__)

    def chunk(self, text: str, metadata: dict | None = None) -> list[dict[str, Any]]:
        if not text or not text.strip():
            return []

        tokens = self.encoder.encode(text)
        if not tokens:
            return []

        step = self.CHUNK_SIZE - self.CHUNK_OVERLAP
        chunks: list[dict[str, Any]] = []
        metadata_payload = dict(metadata or {})

        for start in range(0, len(tokens), step):
            chunk_tokens = tokens[start : start + self.CHUNK_SIZE]
            token_count = len(chunk_tokens)
            if token_count < MIN_CHUNK_TOKEN_COUNT:
                continue
            chunks.append(
                {
                    "text": self.encoder.decode(chunk_tokens),
                    "token_count": token_count,
                    "metadata": dict(metadata_payload),
                }
            )

        total_chunks = len(chunks)
        for index, item in enumerate(chunks):
            item["chunk_index"] = index
            item["total_chunks"] = total_chunks

        return chunks

    def chunk_documents(self, documents: list[dict[str, str]]) -> list[dict[str, Any]]:
        all_chunks: list[dict[str, Any]] = []
        for document in documents:
            metadata = {
                "url": document.get("url"),
                "title": document.get("title"),
                "source": document.get("source"),
            }
            all_chunks.extend(self.chunk(document.get("text", ""), metadata=metadata))
        return all_chunks
