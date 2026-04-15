from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.db.models import ReportStatus
from backend.tools import cache as cache_module
from backend.tools import cleanup as cleanup_module
from backend.tools import embeddings as embeddings_module
from backend.tools import store_manager as store_manager_module
from backend.tools import vector_store as vector_store_module

VECTOR_STORE_TEST_K = 5
THREAD_SAFETY_WORKER_COUNT = 10
THREAD_SAFETY_SLEEP_SECONDS = 0.01
CACHE_HIT_TEXT = "cached text"
CACHE_MISS_TEXT = "missing text"


def _make_store() -> vector_store_module.VectorStore:
    with patch("backend.tools.vector_store.get_embeddings", return_value=Mock()):
        return vector_store_module.VectorStore("job-abc")


def _make_mock_path(*, exists: bool, files: list[int] | None = None) -> Mock:
    path = Mock(spec=Path)
    path.exists.return_value = exists
    path.iterdir.side_effect = lambda: iter([Mock()]) if exists else iter([])
    file_sizes = files or []
    path.rglob.return_value = [
        SimpleNamespace(
            is_file=lambda: True,
            stat=lambda size=size: SimpleNamespace(st_size=size, st_mtime_ns=size * 10),
        )
        for size in file_sizes
    ]
    path.mkdir = Mock()
    return path


def test_load_or_create_loads_existing() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=True)

    with patch.object(vector_store_module, "FAISS") as faiss_cls:
        store.load_or_create()

    faiss_cls.load_local.assert_called_once()


def test_load_or_create_creates_new() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=False)

    with patch.object(vector_store_module, "FAISS") as faiss_cls:
        store.load_or_create()

    assert store.index is None
    faiss_cls.load_local.assert_not_called()


def test_add_chunks_first_time_creates_index() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=False)
    faiss_index = Mock()
    faiss_index.save_local = Mock()

    chunks = [
        {"text": "chunk one", "metadata": {"url": "https://example.com/1"}},
        {"text": "chunk two", "metadata": {"url": "https://example.com/2"}},
        {"text": "chunk three", "metadata": {"url": "https://example.com/3"}},
    ]

    with patch.object(vector_store_module, "FAISS") as faiss_cls:
        faiss_cls.from_documents.return_value = faiss_index

        added_count = store.add_chunks(chunks)

    assert added_count == 3
    faiss_cls.from_documents.assert_called_once()
    faiss_index.save_local.assert_called_once()


def test_add_chunks_existing_index_appends() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=True)
    store.index = Mock()
    store.index.save_local = Mock()

    with patch.object(vector_store_module, "FAISS") as faiss_cls:
        store.add_chunks([{"text": "chunk one", "metadata": {}}])

    store.index.add_documents.assert_called_once()
    store.index.save_local.assert_called_once()
    faiss_cls.from_documents.assert_not_called()


def test_search_returns_sorted_results() -> None:
    store = _make_store()
    first_doc = Mock(page_content="Less relevant", metadata={"url": "https://a.com"})
    second_doc = Mock(page_content="More relevant", metadata={"url": "https://b.com"})
    store.index = Mock()
    store.index.similarity_search_with_score.return_value = [
        (first_doc, 0.9),
        (second_doc, 0.1),
    ]

    results = store.search("query", k=VECTOR_STORE_TEST_K)

    assert [item["score"] for item in results] == [0.1, 0.9]


def test_search_empty_index_returns_empty() -> None:
    store = _make_store()

    assert store.search("query") == []


def test_health_check_loaded() -> None:
    store = _make_store()
    store.index = SimpleNamespace(index=SimpleNamespace(ntotal=4))
    store.index_path = _make_mock_path(exists=True, files=[12, 8])

    health = store.health_check()

    assert health["loaded"] is True
    assert health["vector_count"] == 4
    assert health["index_size_bytes"] == 20


def test_health_check_not_loaded() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=False)

    health = store.health_check()

    assert health["loaded"] is False
    assert health["vector_count"] is None


def test_health_check_never_raises() -> None:
    store = _make_store()
    store.index_path = _make_mock_path(exists=True)

    class BrokenIndex:
        @property
        def index(self):
            raise AttributeError("broken index")

    store.index = BrokenIndex()

    health = store.health_check()

    assert health["loaded"] is False
    assert "error" in health


def test_clear_sets_index_none() -> None:
    store = _make_store()
    store.index = Mock()
    store.index_path = _make_mock_path(exists=True)

    with patch.object(vector_store_module.shutil, "rmtree") as rmtree:
        store.clear()

    assert store.index is None
    rmtree.assert_called_once()


def test_list_sources_deduplicates() -> None:
    store = _make_store()
    store.get_all_metadata = Mock(
        return_value=[
            {"url": "https://b.com"},
            {"url": "https://a.com"},
            {"url": "https://a.com"},
        ]
    )

    assert store.list_sources() == ["https://a.com", "https://b.com"]


def test_merge_increases_vector_count() -> None:
    store = _make_store()
    store.index = Mock()
    store.index.index = SimpleNamespace(ntotal=8)
    store.index.save_local = Mock()
    store.index.merge_from = Mock()
    store.index_path = _make_mock_path(exists=True)
    other_index = Mock()

    def fake_load_or_create(self):
        self.index = other_index

    with patch("backend.tools.vector_store.get_embeddings", return_value=Mock()), patch.object(
        vector_store_module.VectorStore,
        "load_or_create",
        autospec=True,
        side_effect=fake_load_or_create,
    ):
        total_vectors = store.merge("job-other")

    store.index.merge_from.assert_called_once_with(other_index)
    assert total_vectors == 8


def test_refresh_if_stale_reloads_changed_disk_state() -> None:
    store = _make_store()
    store._loaded_signature = (("index.faiss", 1, 10),)
    store._index_signature = Mock(return_value=(("index.faiss", 2, 20),))

    with patch.object(store, "load_or_create") as load_or_create:
        refreshed = store.refresh_if_stale()

    assert refreshed is True
    load_or_create.assert_called_once()


def test_get_creates_new_store() -> None:
    manager = store_manager_module.VectorStoreManager()
    store = Mock()

    with patch.object(store_manager_module, "VectorStore", return_value=store) as vector_store_cls:
        result = manager.get("job-abc")

    assert result is store
    vector_store_cls.assert_called_once_with("job-abc")
    store.load_or_create.assert_called_once()


def test_get_returns_cached_store() -> None:
    manager = store_manager_module.VectorStoreManager()
    store = Mock()

    with patch.object(store_manager_module, "VectorStore", return_value=store) as vector_store_cls:
        first = manager.get("job-abc")
        second = manager.get("job-abc")

    assert first is second
    vector_store_cls.assert_called_once_with("job-abc")


def test_get_refreshes_cached_store_when_auto_load_enabled() -> None:
    manager = store_manager_module.VectorStoreManager()
    store = Mock()

    with patch.object(store_manager_module, "VectorStore", return_value=store):
        manager.get("job-abc")
        store.load_or_create.reset_mock()

        manager.get("job-abc")

    store.refresh_if_stale.assert_called_once()


def test_get_thread_safe() -> None:
    manager = store_manager_module.VectorStoreManager()
    created_stores: list[Mock] = []

    def build_store(index_name: str) -> Mock:
        time.sleep(THREAD_SAFETY_SLEEP_SECONDS)
        store = Mock(name=f"store-{index_name}")
        created_stores.append(store)
        return store

    with patch.object(store_manager_module, "VectorStore", side_effect=build_store) as vector_store_cls:
        with ThreadPoolExecutor(max_workers=THREAD_SAFETY_WORKER_COUNT) as executor:
            futures = [
                executor.submit(manager.get, "job-abc")
                for _ in range(THREAD_SAFETY_WORKER_COUNT)
            ]
            results = [future.result() for future in futures]

    assert len({id(result) for result in results}) == 1
    assert vector_store_cls.call_count == 1
    assert len(created_stores) == 1


def test_release_removes_from_cache() -> None:
    manager = store_manager_module.VectorStoreManager()
    store = Mock()

    with patch.object(store_manager_module, "VectorStore", return_value=store):
        manager.get("job-abc")

    manager.release("job-abc")

    assert manager.list_active() == []


def test_release_does_not_delete_disk() -> None:
    manager = store_manager_module.VectorStoreManager()
    store = Mock()

    with patch.object(store_manager_module, "VectorStore", return_value=store):
        manager.get("job-abc")

    manager.release("job-abc")

    store.clear.assert_not_called()


def test_health_report_returns_all_active() -> None:
    manager = store_manager_module.VectorStoreManager()
    first_store = Mock()
    second_store = Mock()
    first_store.health_check.return_value = {"loaded": True}
    second_store.health_check.return_value = {"loaded": False}

    with patch.object(
        store_manager_module,
        "VectorStore",
        side_effect=[first_store, second_store],
    ):
        manager.get("job-a")
        manager.get("job-b")

    report = manager.health_report()

    assert set(report.keys()) == {"job-a", "job-b"}


def test_get_cache_hit() -> None:
    redis = Mock()
    redis.get.return_value = json.dumps([1.0, 2.0])

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()

    assert cache.get(CACHE_HIT_TEXT) == [1.0, 2.0]


def test_get_cache_miss() -> None:
    redis = Mock()
    redis.get.return_value = None

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()

    assert cache.get(CACHE_MISS_TEXT) is None


def test_set_stores_json() -> None:
    redis = Mock()

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()
        cache.set(CACHE_HIT_TEXT, [1.0, 2.0])

    redis.setex.assert_called_once()
    assert json.loads(redis.setex.call_args.args[2]) == [1.0, 2.0]


def test_get_many_uses_mget() -> None:
    redis = Mock()
    redis.mget.return_value = [json.dumps([1.0]), None, json.dumps([3.0])]

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()
        results = cache.get_many(["a", "b", "c"])

    redis.mget.assert_called_once()
    assert results == {"a": [1.0], "b": None, "c": [3.0]}


def test_set_many_uses_pipeline() -> None:
    pipeline = Mock()
    pipeline.set.return_value = pipeline
    pipeline.expire.return_value = pipeline
    redis = Mock()
    redis.pipeline.return_value = pipeline

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()
        cache.set_many({"a": [1.0], "b": [2.0]})

    redis.pipeline.assert_called_once()
    pipeline.execute.assert_called_once()


def test_cache_error_does_not_raise() -> None:
    redis = Mock()
    redis.get.side_effect = ConnectionError("offline")
    redis.setex.side_effect = ConnectionError("offline")

    with patch.object(cache_module, "get_sync_redis", return_value=redis):
        cache = cache_module.EmbeddingCache()

        assert cache.get("a") is None
        assert cache.set("a", [1.0]) is None


def test_embed_texts_uses_cache_for_known_texts() -> None:
    cache = Mock()
    cache.get_many.return_value = {
        "a": [1.0],
        "b": [2.0],
        "c": None,
    }
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[3.0]]

    with patch.object(embeddings_module, "EmbeddingCache", return_value=cache), patch.object(
        embeddings_module,
        "_get_openai_embeddings",
        return_value=embeddings,
    ):
        results = embeddings_module.embed_texts(["a", "b", "c"])

    embeddings.embed_documents.assert_called_once_with(["c"])
    assert results == [[1.0], [2.0], [3.0]]


def test_embed_texts_stores_new_embeddings_in_cache() -> None:
    cache = Mock()
    cache.get_many.return_value = {"a": None, "b": None}
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[1.0], [2.0]]

    with patch.object(embeddings_module, "EmbeddingCache", return_value=cache), patch.object(
        embeddings_module,
        "_get_openai_embeddings",
        return_value=embeddings,
    ):
        embeddings_module.embed_texts(["a", "b"])

    cache.set_many.assert_called_once_with({"a": [1.0], "b": [2.0]})


def test_embed_texts_returns_correct_order() -> None:
    cache = Mock()
    cache.get_many.return_value = {
        "cached": [10.0],
        "uncached-1": None,
        "uncached-2": None,
    }
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[20.0], [30.0]]

    with patch.object(embeddings_module, "EmbeddingCache", return_value=cache), patch.object(
        embeddings_module,
        "_get_openai_embeddings",
        return_value=embeddings,
    ):
        results = embeddings_module.embed_texts(
            ["cached", "uncached-1", "cached", "uncached-2"]
        )

    assert results == [[10.0], [20.0], [10.0], [30.0]]


def test_get_embeddings_returns_cache_aware_wrapper() -> None:
    raw_embeddings = Mock()
    previous_raw = embeddings_module._openai_embeddings
    previous_cached = embeddings_module._cached_embeddings
    embeddings_module._openai_embeddings = None
    embeddings_module._cached_embeddings = None

    try:
        with patch.object(embeddings_module, "OpenAIEmbeddings", return_value=raw_embeddings):
            wrapped_embeddings = embeddings_module.get_embeddings()
    finally:
        embeddings_module._openai_embeddings = previous_raw
        embeddings_module._cached_embeddings = previous_cached

    assert isinstance(wrapped_embeddings, embeddings_module.CachedEmbeddings)
    assert wrapped_embeddings.underlying_embeddings is raw_embeddings


def _make_cleanup_dir(name: str) -> Mock:
    index_dir = Mock(spec=Path)
    index_dir.name = name
    index_dir.is_dir.return_value = True
    return index_dir


class FakeCleanupSession:
    def __init__(self, reports: dict[uuid.UUID, object]):
        self.reports = reports

    def get(self, model, report_id):
        return self.reports.get(report_id)

    def close(self):
        return None


def _run_cleanup(index_dirs: list[Mock], reports: dict[uuid.UUID, object]) -> tuple[dict[str, int], Mock]:
    base_path = Mock(spec=Path)
    base_path.exists.return_value = True
    base_path.iterdir.return_value = index_dirs
    session = FakeCleanupSession(reports)

    with patch.object(cleanup_module, "Path", return_value=base_path), patch.object(
        cleanup_module,
        "SyncSessionLocal",
        return_value=session,
    ), patch.object(cleanup_module.shutil, "rmtree") as rmtree:
        result = cleanup_module.cleanup_old_indexes()

    return result, rmtree


def test_cleanup_deletes_orphaned_index() -> None:
    orphan_dir = _make_cleanup_dir(str(uuid.uuid4()))

    result, rmtree = _run_cleanup([orphan_dir], {})

    assert result["deleted"] == 1
    rmtree.assert_called_once_with(orphan_dir)


def test_cleanup_deletes_old_done_report() -> None:
    report_id = uuid.uuid4()
    old_report = SimpleNamespace(
        status=ReportStatus.DONE,
        completed_at=datetime.now(timezone.utc) - timedelta(days=8),
    )

    result, rmtree = _run_cleanup([_make_cleanup_dir(str(report_id))], {report_id: old_report})

    assert result["deleted"] == 1
    rmtree.assert_called_once()


def test_cleanup_keeps_recent_done_report() -> None:
    report_id = uuid.uuid4()
    recent_report = SimpleNamespace(
        status=ReportStatus.DONE,
        completed_at=datetime.now(timezone.utc) - timedelta(days=3),
    )

    result, rmtree = _run_cleanup(
        [_make_cleanup_dir(str(report_id))],
        {report_id: recent_report},
    )

    assert result["deleted"] == 0
    rmtree.assert_not_called()


def test_cleanup_keeps_running_report() -> None:
    report_id = uuid.uuid4()
    running_report = SimpleNamespace(
        status=ReportStatus.RUNNING,
        completed_at=None,
    )

    result, rmtree = _run_cleanup(
        [_make_cleanup_dir(str(report_id))],
        {report_id: running_report},
    )

    assert result["deleted"] == 0
    rmtree.assert_not_called()


def test_cleanup_deletes_old_failed_report_without_completed_at() -> None:
    report_id = uuid.uuid4()
    failed_report = SimpleNamespace(
        status=ReportStatus.FAILED,
        completed_at=None,
        updated_at=datetime.now(timezone.utc) - timedelta(days=8),
    )

    result, rmtree = _run_cleanup(
        [_make_cleanup_dir(str(report_id))],
        {report_id: failed_report},
    )

    assert result["deleted"] == 1
    rmtree.assert_called_once()


def test_cleanup_returns_correct_counts() -> None:
    kept_report_id = uuid.uuid4()
    orphan_one = _make_cleanup_dir(str(uuid.uuid4()))
    orphan_two = _make_cleanup_dir(str(uuid.uuid4()))
    old_done_id = uuid.uuid4()
    kept_dir = _make_cleanup_dir(str(kept_report_id))
    old_done_dir = _make_cleanup_dir(str(old_done_id))
    kept_report = SimpleNamespace(
        status=ReportStatus.RUNNING,
        completed_at=None,
    )
    old_done_report = SimpleNamespace(
        status=ReportStatus.DONE,
        completed_at=datetime.now(timezone.utc) - timedelta(days=8),
    )

    result, _ = _run_cleanup(
        [orphan_one, orphan_two, old_done_dir, kept_dir],
        {
            kept_report_id: kept_report,
            old_done_id: old_done_report,
        },
    )

    assert result == {"scanned": 4, "deleted": 3, "errors": 0}
