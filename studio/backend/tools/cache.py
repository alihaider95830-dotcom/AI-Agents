from __future__ import annotations

import hashlib
import json

from backend.core.logging import get_logger
from backend.core.redis_client import get_sync_redis

CACHE_TTL_SECONDS = 3600
CACHE_KEY_PREFIX = "embed_cache"
CACHE_TEXT_ENCODING = "utf-8"


class EmbeddingCache:
    def __init__(self):
        self.redis = get_sync_redis()
        self.logger = get_logger(__name__)

    def _make_key(self, text: str) -> str:
        text_hash = hashlib.sha256(text.encode(CACHE_TEXT_ENCODING)).hexdigest()
        return f"{CACHE_KEY_PREFIX}:{text_hash}"

    def _deserialize_embedding(self, raw_value: str | bytes | None) -> list[float] | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode(CACHE_TEXT_ENCODING)
        return [float(value) for value in json.loads(raw_value)]

    def get(self, text: str) -> list[float] | None:
        try:
            raw_value = self.redis.get(self._make_key(text))
            return self._deserialize_embedding(raw_value)
        except Exception:
            return None

    def set(self, text: str, embedding: list[float]) -> None:
        try:
            self.redis.setex(
                self._make_key(text),
                CACHE_TTL_SECONDS,
                json.dumps(embedding),
            )
        except Exception as exc:
            self.logger.warning("failed to store embedding cache entry: %s", exc)

    def get_many(self, texts: list[str]) -> dict[str, list[float] | None]:
        if not texts:
            return {}

        keys = [self._make_key(text) for text in texts]
        try:
            raw_values = self.redis.mget(keys)
        except Exception:
            return {text: None for text in texts}

        results: dict[str, list[float] | None] = {}
        for text, raw_value in zip(texts, raw_values):
            try:
                results[text] = self._deserialize_embedding(raw_value)
            except Exception:
                results[text] = None
        return results

    def set_many(self, text_embedding_pairs: dict[str, list[float]]) -> None:
        if not text_embedding_pairs:
            return

        try:
            pipeline = self.redis.pipeline()
            for text, embedding in text_embedding_pairs.items():
                key = self._make_key(text)
                pipeline.set(key, json.dumps(embedding))
                pipeline.expire(key, CACHE_TTL_SECONDS)
            pipeline.execute()
        except Exception as exc:
            self.logger.warning("failed to store embedding cache batch: %s", exc)
