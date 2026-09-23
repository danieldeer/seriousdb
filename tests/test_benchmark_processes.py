"""Exercise benchmark workers with real spawned processes and isolated files."""

import json
import os
from threading import Barrier

import pytest

from benchmarks import _processes
from benchmarks._processes import process_pool, run_workers
from benchmarks._support import make_entries
from seriousdb import api
from seriousdb.exceptions import ResourceNotFoundError


@pytest.mark.parametrize("mode", ["load-and-read", "resident-read"])
def test_process_reads_use_distinct_children_and_preserve_file(tmp_path, mode):
    path = tmp_path / "database.json"
    entries = make_entries(11, 32)
    chunks = [entries[index::2] for index in range(2)]
    path.write_text(json.dumps(dict(entries)), encoding="utf-8")
    original = path.read_bytes()

    with process_pool(2) as pool:
        run_workers(
            pool, path, chunks, "preload" if mode == "resident-read" else "ready"
        )
        for _ in range(2):
            results = run_workers(pool, path, chunks, mode)
            assert len({result.pid for result in results}) == 2
            assert all(result.pid != os.getpid() for result in results)
            assert [result.values for result in results] == [
                [value for _, value in chunk] for chunk in chunks
            ]
            assert all(result.key_count == len(entries) for result in results)

    assert path.read_bytes() == original


def test_resident_reads_keep_cache_while_cold_reads_reload(tmp_path):
    path = tmp_path / "database.json"
    entries = (("key", "before"),)
    path.write_text(json.dumps(dict(entries)), encoding="utf-8")

    with process_pool(1) as pool:
        run_workers(pool, path, [entries], "preload")
        path.write_text(json.dumps({"key": "after"}), encoding="utf-8")
        assert run_workers(pool, path, [entries], "resident-read")[0].values == [
            "before"
        ]
        assert run_workers(pool, path, [entries], "load-and-read")[0].values == [
            "after"
        ]


def test_worker_errors_reach_parent_and_pool_cleans_up(tmp_path):
    path = tmp_path / "database.json"
    path.write_text(json.dumps({"present": "value"}), encoding="utf-8")

    with process_pool(2) as pool:
        children = list(pool._pool)
        with pytest.raises(ResourceNotFoundError):
            run_workers(pool, path, [(("missing", "value"),)] * 2, "load-and-read")

    assert all(not child.is_alive() for child in children)


def test_single_process_write_probe_persists_all_updates(tmp_path):
    path = tmp_path / "database.json"
    entries = make_entries(10, 32)
    updates = tuple((key, value[::-1]) for key, value in entries)
    chunks = [updates]
    path.write_text(json.dumps(dict(entries)), encoding="utf-8")

    with process_pool(1) as pool:
        results = run_workers(pool, path, chunks, "write")
        assert [result.values for result in results] == [
            [value for _, value in chunk] for chunk in chunks
        ]

    assert json.loads(path.read_bytes()) == dict(updates)


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_write_worker_returns_windows_replacement_conflict(
    tmp_path, monkeypatch, winerror
):
    path = tmp_path / "database.json"
    updates = (("first", "one"), ("second", "two"))
    error = PermissionError(13, "Access denied", "temporary-file")
    error.filename2 = str(path)
    monkeypatch.setattr(error, "winerror", winerror, raising=False)

    calls = []

    def failed_set(key, value):
        calls.append((key, value))
        raise error

    monkeypatch.setattr(_processes, "_start", Barrier(1), raising=False)
    monkeypatch.setattr(api, "load", lambda _: None)
    monkeypatch.setattr(api, "get", dict(updates).__getitem__)
    monkeypatch.setattr(api, "count", lambda: len(updates))
    monkeypatch.setattr(api, "set", failed_set)
    result = _processes._worker(str(path), updates, "write")
    assert calls == list(updates)
    assert result.values == ["one", "two"]
    assert result.key_count == 2
    assert result.write_error == f"atomic replacement conflict (WinError {winerror})"


@pytest.mark.parametrize("fault", ["other-destination", "other-code", "no-winerror"])
def test_write_worker_propagates_other_permission_errors(tmp_path, monkeypatch, fault):
    path = tmp_path / "database.json"
    entries = (("key", "value"),)
    error = PermissionError(13, "Access denied", "temporary-file")
    error.filename2 = "other-file" if fault == "other-destination" else str(path)
    if fault != "no-winerror":
        monkeypatch.setattr(
            error, "winerror", 123 if fault == "other-code" else 5, raising=False
        )

    def failed_write(*_args):
        raise error

    monkeypatch.setattr(_processes, "_start", Barrier(1), raising=False)
    monkeypatch.setattr(api, "load", lambda _: None)
    monkeypatch.setattr(api, "set", failed_write)
    with pytest.raises(PermissionError):
        _processes._worker(str(path), entries, "write")


@pytest.mark.parametrize("mode", ["load-and-read", "resident-read", "write"])
def test_worker_uses_api_for_load_reads_writes_and_count(tmp_path, monkeypatch, mode):
    path = tmp_path / "database.json"
    entries = (("first", "one"), ("second", "two"))
    calls = []

    def load(filename):
        calls.append(("load", filename))

    def get(key):
        calls.append(("get", key))
        return dict(entries)[key]

    def set_value(key, value):
        calls.append(("set", key, value))
        return value

    def count():
        calls.append(("count",))
        return len(entries)

    monkeypatch.setattr(_processes, "_start", Barrier(1), raising=False)
    monkeypatch.setattr(api, "load", load)
    monkeypatch.setattr(api, "get", get)
    monkeypatch.setattr(api, "set", set_value)
    monkeypatch.setattr(api, "count", count)
    if mode == "resident-read":
        _processes._worker(str(path), entries, "preload")
        assert calls == [("load", str(path))]
        calls.clear()
    result = _processes._worker(str(path), entries, mode)

    expected: list[tuple[str, ...]] = (
        [] if mode == "resident-read" else [("load", str(path))]
    )
    if mode == "write":
        expected.extend(("set", key, value) for key, value in entries)
    expected.extend(("get", key) for key, _ in entries)
    expected.append(("count",))
    assert calls == expected
    assert result.values == [value for _, value in entries]
    assert result.key_count == len(entries)
