"""Tests for the Cache interface and basic database operations."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest import MonkeyPatch

from seriousdb.cache import COMPACTION_THRESHOLD, Cache, require_db
from seriousdb.exceptions import ResourceNotFoundError, ServiceUnavailableError
from seriousdb.wal import SetEntry


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / ".sdb"


@pytest.fixture
def cache(db_path):
    cache = Cache()
    cache.load(str(db_path))
    return cache


def test_cache_starts_unloaded():
    cache = Cache()

    assert cache.db is None
    assert cache.filename is None


def test_insert_stores_new_value(cache):
    value, is_new_key = cache.insert("name", "Alice")

    assert value == "Alice"
    assert is_new_key
    assert cache.db == {"name": "Alice"}


def test_insert_overwrites_existing_value(cache):
    cache.insert("name", "Alice")

    value, is_new_key = cache.insert("name", "Bob")

    assert value == "Bob"
    assert not is_new_key
    assert cache.db == {"name": "Bob"}


def test_select_returns_stored_value(cache):
    cache.insert("name", "Alice")

    assert cache.select("name") == "Alice"


def test_select_missing_key_raises(cache):
    with pytest.raises(
        ResourceNotFoundError,
        match="No value set for key missing",
    ):
        cache.select("missing")


def test_delete_returns_previous_value_and_removes_key(cache):
    cache.insert("name", "Alice")

    value = cache.delete("name")

    assert value == "Alice"
    assert cache.db == {}


def test_delete_missing_key_raises(cache):
    with pytest.raises(ResourceNotFoundError, match="No value set for key missing"):
        cache.delete("missing")


def test_operations_require_loaded_database():
    cache = Cache()

    with pytest.raises(ServiceUnavailableError):
        cache.insert("name", "Alice")

    with pytest.raises(ServiceUnavailableError):
        cache.select("name")

    with pytest.raises(ServiceUnavailableError):
        cache.delete("name")


def test_load_creates_missing_database(db_path):
    cache = Cache()

    cache.load(str(db_path))

    assert db_path.exists()
    assert cache.filename == str(db_path)
    assert cache.db == {}


def test_load_reads_existing_database(db_path):
    db_path.write_text(json.dumps({"name": "Alice"}))

    cache = Cache()
    cache.load(str(db_path))

    assert cache.db == {"name": "Alice"}
    assert cache.filename == str(db_path)


def test_load_replaces_current_data(cache, tmp_path):
    cache.insert("name", "Alice")

    other_path = tmp_path / "other.sdb"
    other_path.write_text(json.dumps({"language": "Python"}))

    cache.load(str(other_path))

    assert cache.db == {"language": "Python"}
    assert cache.filename == str(other_path)


def test_load_corrupt_database_starts_fresh(db_path):
    db_path.write_bytes(b"not valid json")

    cache = Cache()
    cache.load(str(db_path))

    assert cache.db == {}
    assert db_path.exists()
    assert list(db_path.parent.glob(".sdb.corrupt-*"))


def test_load_rejects_non_object_json(db_path):
    db_path.write_text(json.dumps(["not", "a", "database"]))

    cache = Cache()
    cache.load(str(db_path))

    assert cache.db == {}
    assert db_path.exists()
    assert list(db_path.parent.glob(".sdb.corrupt-*"))


def test_require_db_returns_loaded_database(cache):
    assert require_db(cache) is cache.db


def test_require_db_raises_when_database_is_not_loaded():
    cache = Cache()
    cache.filename = ".sdb"

    with pytest.raises(
        ServiceUnavailableError,
        match=r"\.sdb",
    ):
        require_db(cache)


def test_compaction_triggers_at_write_threshold(db_path):
    """Compact the database once COMPACTION_THRESHOLD writes have occurred."""
    cache = Cache()
    cache.load(str(db_path))

    for i in range(COMPACTION_THRESHOLD):
        cache.insert(f"key_{i}", f"value_{i}")

    assert cache.wal is not None

    with open(db_path, "rb") as f:
        on_disk = json.loads(f.read().decode())

    assert on_disk == {f"key_{i}": f"value_{i}" for i in range(COMPACTION_THRESHOLD)}

    with open(cache.wal.filename, "rb") as f:
        assert f.read() == b""


def test_compaction_does_not_trigger_before_write_threshold(db_path):
    """Leave writes in the WAL until COMPACTION_THRESHOLD is reached."""
    cache = Cache()
    cache.load(str(db_path))

    for i in range(COMPACTION_THRESHOLD - 1):
        cache.insert(f"key_{i}", f"value_{i}")

    assert cache.wal is not None

    with open(db_path, "rb") as f:
        on_disk = json.loads(f.read().decode())

    assert on_disk == {}

    with open(cache.wal.filename, "rb") as f:
        wal_lines = f.read().decode().splitlines()

    assert len(wal_lines) == COMPACTION_THRESHOLD - 1


def test_compaction_counter_resets_after_compacting(db_path):
    """Reset the WAL write counter after compaction."""
    cache = Cache()
    cache.load(str(db_path))

    for i in range(COMPACTION_THRESHOLD):
        cache.insert(f"key_{i}", f"value_{i}")

    cache.insert("one_more", "value")

    assert cache.wal is not None

    with open(cache.wal.filename, "rb") as f:
        wal_lines = f.read().decode().splitlines()

    assert wal_lines == [json.dumps(SetEntry(key="one_more", value="value").to_dict())]


def test_insert_succeeds_when_compaction_fails(db_path, monkeypatch):
    """Keep a successfully appended write when a later compaction fails."""
    cache = Cache()
    cache.load(str(db_path))

    assert cache.db is not None

    for index in range(COMPACTION_THRESHOLD - 1):
        cache.insert(f"key-{index}", str(index))

    def boom(_data):
        raise OSError("simulated disk-full during compaction")

    assert cache._persistence is not None
    monkeypatch.setattr(cache._persistence, "_compact", boom)

    value, is_new_key = cache.insert("name", "Alice")

    assert value == "Alice"
    assert is_new_key
    assert cache.db["name"] == "Alice"


def test_replay_recovers_from_torn_last_wal_entry(db_path):
    """Ignore a truncated final WAL record while replaying complete records."""
    cache = Cache()
    cache.load(str(db_path))

    cache.insert("a", "1")
    cache.insert("b", "2")

    assert cache.wal is not None

    with open(cache.wal.filename, "rb") as f:
        wal_bytes = f.read()

    with open(cache.wal.filename, "wb") as f:
        f.write(wal_bytes[:-3])

    reloaded = Cache()
    reloaded.load(str(db_path))

    assert reloaded.db == {"a": "1"}


def test_replay_is_idempotent_after_interrupted_compaction(db_path):
    """Replay WAL entries safely when the snapshot was replaced before WAL clear."""
    cache = Cache()
    cache.load(str(db_path))

    cache.insert("a", "1")
    cache.insert("b", "2")

    assert cache.db is not None

    with open(db_path, "wb") as f:
        f.write(json.dumps(cache.db).encode())

    reloaded = Cache()
    reloaded.load(str(db_path))

    assert reloaded.db == {"a": "1", "b": "2"}


def test_insert_leaves_state_unchanged_when_wal_append_fails(db_path, monkeypatch):
    """Do not mutate memory when the WAL append fails."""
    cache = Cache()
    cache.load(str(db_path))

    assert cache.db is not None
    assert cache.wal is not None

    def boom(op):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(cache.wal, "append", boom)

    with pytest.raises(OSError):
        cache.insert("name", "Alice")

    assert "name" not in cache.db

    reloaded = Cache()
    reloaded.load(str(db_path))

    assert reloaded.db is not None
    assert "name" not in reloaded.db


def test_delete_leaves_state_unchanged_when_wal_append_fails(db_path, monkeypatch):
    """Do not mutate memory when the WAL append fails during deletion."""
    cache = Cache()
    cache.load(str(db_path))

    assert cache.db is not None
    assert cache.wal is not None

    cache.insert("name", "Alice")

    def boom(op):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(cache.wal, "append", boom)

    with pytest.raises(OSError):
        cache.delete("name")

    assert cache.db["name"] == "Alice"

    reloaded = Cache()
    reloaded.load(str(db_path))

    assert reloaded.db is not None
    assert reloaded.db["name"] == "Alice"


def test_replay_repairs_torn_wal_before_later_appends(db_path):
    """Remove a torn final record so later WAL appends remain valid."""
    cache = Cache()
    cache.load(str(db_path))

    assert cache.wal is not None

    cache.insert("a", "1")
    cache.insert("b", "2")

    with open(cache.wal.filename, "rb") as f:
        wal_bytes = f.read()

    with open(cache.wal.filename, "wb") as f:
        f.write(wal_bytes[:-3])

    recovered = Cache()
    recovered.load(str(db_path))

    assert recovered.wal is not None
    assert recovered.db == {"a": "1"}

    with open(recovered.wal.filename, "rb") as f:
        repaired_bytes = f.read()

    assert repaired_bytes == (
        json.dumps(SetEntry(key="a", value="1").to_dict()).encode() + b"\n"
    )

    recovered.insert("c", "3")

    final = Cache()
    final.load(str(db_path))

    assert final.db == {"a": "1", "c": "3"}


def boom(*args, **kwargs):
    raise RuntimeError("simulated crash mid-compact")


def test_write_default_failure_does_not_create_destination(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    db_file = tmp_path / ".sdb"
    monkeypatch.setattr(json, "dumps", boom)

    cache = Cache()
    with pytest.raises(RuntimeError):
        cache.load(str(db_file))

    assert not db_file.exists()


def test_compact_failure_does_not_corrupt_existing_snapshot(db_path, monkeypatch):
    """A failed compaction must not corrupt the snapshot file already on disk."""
    cache = Cache()
    cache.load(str(db_path))
    cache.insert("name", "Alice")
    assert cache._persistence is not None
    assert cache.db is not None
    with cache.lock, cache._persistence.write_state(cache.db) as state:
        cache._persistence._compact(state.data)
    original_content = db_path.read_bytes()

    cache.insert("name", "Bob")

    monkeypatch.setattr(json, "dumps", boom)

    with (
        cache.lock,
        cache._persistence.write_state(cache.db) as state,
        pytest.raises(RuntimeError),
    ):
        cache._persistence._compact(state.data)

    assert db_path.read_bytes() == original_content


def test_load_corrupt_backup_collision_preserves_backups(db_path, monkeypatch):
    """Recovering from corruption twice with the same timestamp keeps both backups."""
    first_payload = b"FIRST_CORRUPT_PAYLOAD"
    second_payload = b"SECOND_CORRUPT_PAYLOAD"

    db_path.write_bytes(first_payload)

    fixed_timestamp = 1700000000.0
    monkeypatch.setattr("seriousdb.persistence.time.time", lambda: fixed_timestamp)

    cache = Cache()
    cache.load(str(db_path))

    db_path.write_bytes(second_payload)

    cache.load(str(db_path))

    backup_1 = db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}"
    backup_2 = db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}-1"

    assert backup_1.exists()
    assert backup_2.exists()
    assert backup_1.read_bytes() == first_payload
    assert backup_2.read_bytes() == second_payload

    assert cache.db == {}
    assert json.loads(db_path.read_bytes()) == {}

    cache.insert("test_key", "test_val")

    reloaded = Cache()
    reloaded.load(str(db_path))
    assert reloaded.db == {"test_key": "test_val"}


def test_load_corrupt_backup_with_existing_collision_suffixes(db_path, monkeypatch):
    """Recovery picks the next free numeric suffix when earlier ones exist."""
    fixed_timestamp = 1700000000.0
    monkeypatch.setattr("seriousdb.persistence.time.time", lambda: fixed_timestamp)

    existing_backups = [
        db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}",
        db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}-1",
        db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}-2",
    ]
    for i, backup in enumerate(existing_backups):
        backup.write_bytes(f"EXISTING_PAYLOAD_{i}".encode())

    third_payload = b"THIRD_CORRUPT_PAYLOAD"
    db_path.write_bytes(third_payload)

    cache = Cache()
    cache.load(str(db_path))

    new_backup = db_path.parent / f"{db_path.name}.corrupt-{int(fixed_timestamp)}-3"
    assert new_backup.exists()
    assert new_backup.read_bytes() == third_payload

    for i, backup in enumerate(existing_backups):
        assert backup.read_bytes() == f"EXISTING_PAYLOAD_{i}".encode()

    assert cache.db == {}
    assert json.loads(db_path.read_bytes()) == {}


def test_compaction_threshold_counts_replayed_writes_across_restart(db_path):
    """Writes recovered by replay must still count toward the next compaction threshold, the counter shouldn't
    reset to zero just because the process restarted.
    """
    cache = Cache()
    cache.load(str(db_path))
    for i in range(COMPACTION_THRESHOLD - 1):
        cache.insert(f"key_{i}", f"value_{i}")

    reloaded = Cache()
    reloaded.load(str(db_path))

    reloaded.insert("one_more", "value")

    with open(db_path, "rb") as f:
        on_disk = json.loads(f.read().decode())
    assert len(on_disk) == COMPACTION_THRESHOLD

    assert reloaded.wal is not None
    with open(reloaded.wal.filename, "rb") as f:
        assert f.read() == b""


def test_cache_unloaded_operations_raise_service_unavailable():
    cache = Cache()

    with pytest.raises(ServiceUnavailableError):
        cache.exists("key")

    with pytest.raises(ServiceUnavailableError):
        _ = "key" in cache

    with pytest.raises(ServiceUnavailableError):
        cache.count()

    with pytest.raises(ServiceUnavailableError):
        _ = len(cache)

    with pytest.raises(ServiceUnavailableError):
        cache.get_all()

    with pytest.raises(ServiceUnavailableError):
        cache.get_bulk(["key"])


def test_cache_exists_and_contains(cache):
    assert not cache.exists("name")
    assert "name" not in cache

    cache.insert("name", "Alice")

    assert cache.exists("name")
    assert "name" in cache


def test_cache_count_and_len(cache):
    assert cache.count() == 0
    assert len(cache) == 0

    cache.insert("a", "1")
    cache.insert("b", "2")

    assert cache.count() == 2
    assert len(cache) == 2

    cache.delete("a")

    assert cache.count() == 1
    assert len(cache) == 1


def test_cache_get_all_returns_snapshot_copy(cache):
    cache.insert("k1", "v1")
    cache.insert("k2", "v2")

    snapshot = cache.get_all()
    assert snapshot == {"k1": "v1", "k2": "v2"}

    # Mutating snapshot should not affect cache
    snapshot["k1"] = "mutated"
    assert cache.select("k1") == "v1"

    # Mutating cache should not affect previously taken snapshot
    cache.insert("k1", "v1_updated")
    cache.insert("k3", "v3")
    cache.delete("k2")
    assert snapshot == {"k1": "mutated", "k2": "v2"}


def test_cache_get_bulk_with_iterable(cache):
    cache.insert("k1", "v1")
    cache.insert("k2", "v2")
    cache.insert("k3", "v3")

    # Multiple existing keys
    assert cache.get_bulk(["k1", "k2"]) == {"k1": "v1", "k2": "v2"}

    # Several existing keys mixed with missing keys
    assert cache.get_bulk(["k1", "missing", "k3"]) == {"k1": "v1", "k3": "v3"}

    # Edge cases: empty iterable, missing keys only, duplicate keys
    assert cache.get_bulk([]) == {}
    assert cache.get_bulk(["missing_1", "missing_2"]) == {}
    assert cache.get_bulk(["k1", "k1"]) == {"k1": "v1"}

    def key_gen():
        yield "k2"
        yield "k3"
        yield "missing"

    assert cache.get_bulk(key_gen()) == {"k2": "v2", "k3": "v3"}


def test_cache_query_operations_acquire_lock(cache):
    mock_lock = MagicMock(wraps=cache.lock)
    with patch.object(cache, "lock", mock_lock):
        cache.exists("k")
        assert mock_lock.__enter__.call_count == 1

    mock_lock = MagicMock(wraps=cache.lock)
    with patch.object(cache, "lock", mock_lock):
        cache.get_all()
        assert mock_lock.__enter__.call_count == 1

    mock_lock = MagicMock(wraps=cache.lock)
    with patch.object(cache, "lock", mock_lock):
        cache.get_bulk(["k"])
        assert mock_lock.__enter__.call_count == 1

    mock_lock = MagicMock(wraps=cache.lock)
    with patch.object(cache, "lock", mock_lock):
        cache.count()
        assert mock_lock.__enter__.call_count == 1


def test_cache_get_bulk_materializes_generator_outside_lock(cache):
    cache.insert("k1", "v1")

    yielded_while_unlocked = []

    def key_gen():
        yielded_while_unlocked.append(not cache.lock.locked())
        yield "k1"
        yielded_while_unlocked.append(not cache.lock.locked())
        yield "missing"

    result = cache.get_bulk(key_gen())
    assert result == {"k1": "v1"}
    assert yielded_while_unlocked == [True, True]
