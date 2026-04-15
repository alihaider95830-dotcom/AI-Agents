from __future__ import annotations

import threading

from backend.core.logging import get_logger
from backend.tools.vector_store import VectorStore


class VectorStoreManager:
    def __init__(self):
        self._stores: dict[str, VectorStore] = {}
        self._lock = threading.Lock()
        self.logger = get_logger(__name__)

    def get(self, index_name: str, auto_load: bool = True) -> VectorStore:
        with self._lock:
            store = self._stores.get(index_name)
            if store is None:
                store = VectorStore(index_name)
                if auto_load:
                    store.load_or_create()
                self._stores[index_name] = store
                return store

            if auto_load:
                store.refresh_if_stale()
            return store

    def release(self, index_name: str) -> None:
        with self._lock:
            removed = self._stores.pop(index_name, None)

        if removed is not None:
            self.logger.info("Released store %s from memory", index_name)

    def release_all(self) -> None:
        for index_name in self.list_active():
            self.release(index_name)

    def list_active(self) -> list[str]:
        with self._lock:
            return sorted(self._stores.keys())

    def health_report(self) -> dict[str, dict]:
        with self._lock:
            active_stores = dict(self._stores)

        return {
            index_name: store.health_check()
            for index_name, store in active_stores.items()
        }


store_manager = VectorStoreManager()
