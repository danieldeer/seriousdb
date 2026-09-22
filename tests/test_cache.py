import json
import os
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from seriousdb.cache import Cache


def boom(*args, **kwargs):
    raise RuntimeError("simulated crash mid-flush")


def test_write_default_uses_fsync(tmp_path: Path, monkeypatch: MonkeyPatch):
    db_file = tmp_path / ".sdb"
    fsync_calls: list[int] = []
    real_fsync = os.fsync

    def tracking_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", tracking_fsync)

    cache = Cache()
    cache.load(str(db_file))

    assert fsync_calls, "expected fsync when creating a new empty database"
    assert db_file.exists()
    assert json.loads(db_file.read_bytes()) == {}
    assert cache.db == {}


def test_flush_failure_does_not_corrupt_existing_file(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    db_file = tmp_path / ".sdb"
    cache = Cache()
    cache.load(str(db_file))
    cache.insert("name", "Alice")
    cache.flush()
    original_content = db_file.read_bytes()

    cache.insert("name", "Bob")

    monkeypatch.setattr(json, "dumps", boom)

    with pytest.raises(RuntimeError):
        cache.flush()

    assert db_file.read_bytes() == original_content


def test_load_corrupt_backup_collision_preserves_backups(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    db_file = tmp_path / "database.sdb"
    first_payload = b"FIRST_CORRUPT_PAYLOAD"
    second_payload = b"SECOND_CORRUPT_PAYLOAD"

    # 1. Create a temporary database file and write FIRST_CORRUPT_PAYLOAD
    db_file.write_bytes(first_payload)

    # 2. Freeze/mock the timestamp used for backup naming
    fixed_timestamp = 1700000000.0
    monkeypatch.setattr("seriousdb.cache.time.time", lambda: fixed_timestamp)

    # 3. Trigger normal corruption recovery
    cache = Cache()
    cache.load(str(db_file))

    # 4. Write SECOND_CORRUPT_PAYLOAD to the same database path
    db_file.write_bytes(second_payload)

    # 5. Trigger recovery again with the same timestamp
    cache.load(str(db_file))

    # 6. Assert that two distinct backup files exist and neither was overwritten
    backup_1 = tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}"
    backup_2 = tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}-1"

    assert backup_1.exists(), f"Expected {backup_1} to exist"
    assert backup_2.exists(), f"Expected {backup_2} to exist"

    assert backup_1.read_bytes() == first_payload
    assert backup_2.read_bytes() == second_payload

    # 7. Assert that the active database is valid after recovery
    assert cache.db == {}
    assert json.loads(db_file.read_bytes()) == {}
    cache.insert("test_key", "test_val")
    cache.flush()
    assert json.loads(db_file.read_bytes()) == {"test_key": "test_val"}


def test_load_corrupt_backup_with_existing_collision_suffixes(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    db_file = tmp_path / "database.sdb"
    fixed_timestamp = 1700000000.0
    monkeypatch.setattr("seriousdb.cache.time.time", lambda: fixed_timestamp)

    # Pre-create multiple collision suffixes:
    # .corrupt-1700000000, .corrupt-1700000000-1, .corrupt-1700000000-2
    existing_backups = [
        tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}",
        tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}-1",
        tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}-2",
    ]
    for i, backup in enumerate(existing_backups):
        backup.write_bytes(f"EXISTING_PAYLOAD_{i}".encode())

    # Write corrupt payload and trigger recovery with the same timestamp
    third_payload = b"THIRD_CORRUPT_PAYLOAD"
    db_file.write_bytes(third_payload)

    cache = Cache()
    cache.load(str(db_file))

    # Verify implementation chooses another unused path safely (-3)
    new_backup = tmp_path / f"database.sdb.corrupt-{int(fixed_timestamp)}-3"
    assert new_backup.exists(), f"Expected {new_backup} to exist"
    assert new_backup.read_bytes() == third_payload

    # Verify all existing backups were preserved
    for i, backup in enumerate(existing_backups):
        assert backup.read_bytes() == f"EXISTING_PAYLOAD_{i}".encode()

    assert cache.db == {}
    assert json.loads(db_file.read_bytes()) == {}
