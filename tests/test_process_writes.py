"""Regression tests for independent caches writing the same database."""

import multiprocessing

import pytest

import seriousdb.persistence as persistence_module
import seriousdb.wal as wal_module
from seriousdb.cache import COMPACTION_THRESHOLD, Cache
from seriousdb.exceptions import ResourceNotFoundError


def _write_in_process(path, prefix, ready, start):
    cache = Cache()
    cache.load(path)
    ready.put(prefix)
    if not start.wait(10):
        raise TimeoutError("writer did not start")
    for index in range(COMPACTION_THRESHOLD + 10):
        cache.insert(f"{prefix}-{index}", str(index))


def test_stale_cache_cannot_compact_away_another_writers_entry(tmp_path):
    path = str(tmp_path / "shared.sdb")
    first = Cache()
    second = Cache()
    first.load(path)
    second.load(path)

    second.insert("other", "durable")
    for index in range(COMPACTION_THRESHOLD):
        first.insert(f"first-{index}", str(index))

    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.select("other") == "durable"
    assert reloaded.count() == COMPACTION_THRESHOLD + 1


def test_symlink_alias_uses_target_database_and_lock(tmp_path):
    target = tmp_path / "target.sdb"
    alias = tmp_path / "alias.sdb"
    first = Cache()
    first.load(str(target))
    try:
        alias.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    second = Cache()
    second.load(str(alias))
    assert second.filename == first.filename
    second.insert("from-alias", "kept")
    for index in range(COMPACTION_THRESHOLD):
        first.insert(f"from-target-{index}", str(index))

    reloaded = Cache()
    reloaded.load(str(target))
    assert reloaded.select("from-alias") == "kept"
    assert alias.is_symlink()


def test_delete_uses_latest_durable_value(tmp_path):
    path = str(tmp_path / "shared.sdb")
    first = Cache()
    second = Cache()
    first.load(path)
    second.load(path)

    first.insert("key", "old")
    second.insert("key", "new")
    assert first.delete("key") == "new"
    reloaded = Cache()
    reloaded.load(path)
    with pytest.raises(ResourceNotFoundError):
        reloaded.select("key")


def test_unexpected_compaction_failure_keeps_refreshed_cache_consistent(
    tmp_path, monkeypatch
):
    path = str(tmp_path / "shared.sdb")
    first = Cache()
    second = Cache()
    first.load(path)
    second.load(path)
    expected = {
        f"other-{index}": str(index) for index in range(COMPACTION_THRESHOLD - 1)
    }
    for key, value in expected.items():
        second.insert(key, value)

    def fail(_data):
        raise RuntimeError("unexpected compaction failure")

    assert first._persistence is not None
    with monkeypatch.context() as patch:
        patch.setattr(first._persistence, "_compact", fail)
        with pytest.raises(RuntimeError, match="unexpected compaction failure"):
            first.insert("mine", "kept")

    first.insert("next", "kept")
    expected.update({"mine": "kept", "next": "kept"})
    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.db == expected


def test_failed_append_keeps_local_view_and_releases_process_lock(
    tmp_path, monkeypatch
):
    path = str(tmp_path / "shared.sdb")
    first = Cache()
    second = Cache()
    first.load(path)
    second.load(path)
    second.insert("other", "durable")
    assert first.db == {}

    assert first.wal is not None

    def fail(_entry):
        raise OSError("simulated WAL failure")

    monkeypatch.setattr(first.wal, "append", fail)
    with pytest.raises(OSError, match="simulated WAL failure"):
        first.insert("mine", "lost")
    assert first.db == {}

    second.insert("later", "durable")
    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.db == {"other": "durable", "later": "durable"}


def test_new_wal_is_durable_before_first_entry_is_written(tmp_path, monkeypatch):
    cache = Cache()
    cache.load(str(tmp_path / "shared.sdb"))

    def fail(_path):
        raise OSError("directory sync failed")

    monkeypatch.setattr(wal_module, "_sync_parent_directory", fail, raising=False)
    with pytest.raises(OSError, match="directory sync failed"):
        cache.insert("key", "value")
    assert cache.db == {}
    reloaded = Cache()
    reloaded.load(str(tmp_path / "shared.sdb"))
    assert reloaded.db == {}


def test_snapshot_sync_failure_preserves_wal(tmp_path, monkeypatch):
    path = str(tmp_path / "shared.sdb")
    cache = Cache()
    cache.load(path)

    def fail(_path):
        raise OSError("directory sync failed")

    monkeypatch.setattr(persistence_module, "_sync_parent_directory", fail)
    for index in range(COMPACTION_THRESHOLD):
        cache.insert(f"key-{index}", str(index))

    assert cache.wal is not None
    assert len(cache.wal.replay()) == COMPACTION_THRESHOLD
    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.count() == COMPACTION_THRESHOLD


def test_wal_clear_sync_failure_allows_later_writes(tmp_path, monkeypatch):
    path = str(tmp_path / "shared.sdb")
    cache = Cache()
    cache.load(path)
    for index in range(COMPACTION_THRESHOLD - 1):
        cache.insert(f"key-{index}", str(index))

    sync_attempts = []

    def fail(_path):
        sync_attempts.append(_path)
        raise OSError("directory sync failed")

    with monkeypatch.context() as patch:
        patch.setattr(wal_module, "_sync_parent_directory", fail)
        cache.insert("last-before-compact", "kept")

    assert len(sync_attempts) == 1
    cache.insert("after-failed-clear", "kept")
    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.count() == COMPACTION_THRESHOLD + 1
    assert reloaded.select("last-before-compact") == "kept"
    assert reloaded.select("after-failed-clear") == "kept"


def test_concurrent_processes_keep_every_successful_write(tmp_path):
    path = str(tmp_path / "shared.sdb")
    context = multiprocessing.get_context("spawn")
    ready = context.Queue()
    start = context.Event()
    processes = [
        context.Process(target=_write_in_process, args=(path, prefix, ready, start))
        for prefix in ("one", "two", "three")
    ]
    try:
        for process in processes:
            process.start()
        for _ in processes:
            ready.get(timeout=10)
        start.set()
        for process in processes:
            process.join(timeout=30)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()

    reloaded = Cache()
    reloaded.load(path)
    assert reloaded.count() == 3 * (COMPACTION_THRESHOLD + 10)
