"""Fault injection for benchmark checks, without timing or optional plugins."""

import json
from contextlib import nullcontext
from inspect import signature
from types import SimpleNamespace

import pytest

from benchmarks import (
    _processes,
    test_concurrency,
    test_persistence,
    test_processes,
    test_reads,
    test_workloads,
)
from benchmarks._processes import WorkerResult
from benchmarks._support import load_cache, make_entries, write_database
from seriousdb.cache import Cache


class Rounds:
    """Exercise pedantic callbacks, including disabled mode's skipped teardown."""

    def __init__(self, disabled):
        self.disabled = disabled
        self.extra_info = {}

    def pedantic(
        self, target, args=(), setup=None, teardown=None, rounds=1, warmup_rounds=0
    ):
        for _ in range(1 if self.disabled else warmup_rounds + rounds):
            if setup:
                setup()
            result = target(*args)
            if teardown and not self.disabled:
                teardown(*args)
        return result


@pytest.mark.parametrize(
    ("bad_call", "disabled"), [(1, False), (2, False), (3, False), (1, True)]
)
@pytest.mark.parametrize(
    ("module", "scenario", "operation"),
    [
        (test_reads, "test_load_and_read_by_key", "load_and_read"),
        (test_reads, "test_load_file", "load_cache"),
        (test_reads, "test_resident_read", "read_resident"),
        (test_workloads, "test_mixed_resident", "run_operations"),
        (test_concurrency, "test_shared_cache_threads", "run_operations"),
    ],
    ids=["load-and-read", "load-file", "resident-read", "mixed", "threads"],
)
def test_every_round_rejects_wrong_read_results(
    tmp_path, monkeypatch, module, scenario, operation, bad_call, disabled
):
    path = tmp_path / "benchmark.json"
    entries = make_entries(100, 32)
    write_database(path, entries)
    cache = load_cache(str(path))
    original = getattr(module, operation)
    calls = 0

    def faulty_operation(*args):
        nonlocal calls
        calls += 1
        result = original(*args)
        if calls == bad_call:
            if isinstance(result, Cache):
                result.insert(entries[0][0], "incorrect value")
            else:
                result[0] = "incorrect value"
        return result

    monkeypatch.setattr(module, operation, faulty_operation)
    arguments = {
        "benchmark": Rounds(disabled),
        "loaded_cache": cache,
        "database_file": path,
        "entries": entries,
        "measured_rounds": 3,
        "workers": 1,
    }
    test = getattr(module, scenario)
    with pytest.raises(AssertionError):
        test(**{name: arguments[name] for name in signature(test).parameters})
    assert calls == bad_call


@pytest.mark.parametrize("mode", ["load-and-read", "resident-read"])
@pytest.mark.parametrize("fault", ["value", "count", "pid", "file"])
@pytest.mark.parametrize(
    ("bad_call", "disabled"),
    [(1, False), (2, False), (3, False), (4, False), (1, True)],
)
def test_process_reads_verify_every_round(
    tmp_path, monkeypatch, mode, fault, bad_call, disabled
):
    path = tmp_path / "benchmark.json"
    entries = make_entries(10, 32)
    calls = 0

    def run(_pool, database_file, chunks, operation):
        nonlocal calls
        if operation in ("ready", "preload"):
            return []
        calls += 1
        results = [
            WorkerResult(i, [value for _, value in chunk], len(entries))
            for i, chunk in enumerate(chunks)
        ]
        if calls == bad_call:
            if fault == "value":
                results[0].values[0] = "wrong value"
            elif fault == "count":
                results[0] = results[0]._replace(key_count=len(entries) + 1)
            elif fault == "pid":
                results[0] = results[0]._replace(pid=results[1].pid)
            else:
                database_file.write_text("{}", encoding="utf-8")
        return results

    monkeypatch.setattr(_processes, "process_pool", lambda _: nullcontext())
    monkeypatch.setattr(_processes, "run_workers", run)
    with pytest.raises(AssertionError):
        test_processes.test_process_reads(Rounds(disabled), path, entries, 3, 2, mode)
    assert calls == bad_call


@pytest.mark.parametrize("disabled", [False, True])
@pytest.mark.parametrize("processes", [1, 2])
@pytest.mark.parametrize("persisted", [b"{}", b"not JSON", b"\xff"])
def test_process_write_failures_are_reported(
    tmp_path, monkeypatch, disabled, processes, persisted
):
    path = tmp_path / "benchmark.json"
    entries = make_entries(10, 32)
    benchmark = Rounds(disabled)
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))

    def run(_pool, database_file, chunks, mode):
        if mode == "ready":
            return []
        assert load_cache(str(database_file)).db == dict(entries)
        database_file.write_bytes(persisted)
        return [
            WorkerResult(i, [value for _, value in chunk], len(entries))
            for i, chunk in enumerate(chunks)
        ]

    monkeypatch.setattr(_processes, "process_pool", lambda _: nullcontext())
    monkeypatch.setattr(_processes, "run_workers", run)
    failure = pytest.fail.Exception if processes == 1 else pytest.xfail.Exception
    with pytest.raises(failure):
        test_processes.test_process_writes(
            benchmark, path, entries, 3, processes, request
        )
    assert path.read_bytes() == persisted
    if processes > 1:
        assert benchmark.extra_info["correctness"] == "failed"
        assert benchmark.extra_info["persistence_failures"]


@pytest.mark.parametrize("processes", [1, 2])
@pytest.mark.parametrize("disabled", [False, True])
def test_process_write_conflicts_are_reported_even_when_file_is_correct(
    tmp_path, monkeypatch, processes, disabled
):
    entries = make_entries(10, 32)
    benchmark = Rounds(disabled)
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))

    def run(_pool, path, chunks, mode):
        if mode == "ready":
            return []
        path.write_text(json.dumps(dict(item for chunk in chunks for item in chunk)))
        return [
            WorkerResult(
                i,
                [value for _, value in chunk],
                len(entries),
                "atomic replacement conflict (WinError 5)",
            )
            for i, chunk in enumerate(chunks)
        ]

    monkeypatch.setattr(_processes, "process_pool", lambda _: nullcontext())
    monkeypatch.setattr(_processes, "run_workers", run)
    failure = pytest.fail.Exception if processes == 1 else pytest.xfail.Exception
    with pytest.raises(failure, match="atomic replacement conflict"):
        test_processes.test_process_writes(
            benchmark, tmp_path / "database.json", entries, 3, processes, request
        )
    if processes > 1:
        assert benchmark.extra_info["correctness"] == "failed"
        assert benchmark.extra_info["persistence_failures"] == [
            "atomic replacement conflict (WinError 5)"
        ]


@pytest.mark.parametrize("entry_count", [10, 150])
def test_process_api_writes_bound_work_and_preserve_other_keys(
    tmp_path, monkeypatch, entry_count
):
    entries = make_entries(entry_count, 32)
    benchmark = Rounds(True)
    request = SimpleNamespace(config=SimpleNamespace(getoption=lambda _: True))

    def run(_pool, path, chunks, mode):
        if mode == "ready":
            return []
        assert sum(map(len, chunks)) == min(100, entry_count)
        persisted = json.loads(path.read_bytes())
        persisted.update(item for chunk in chunks for item in chunk)
        path.write_text(json.dumps(persisted))
        return [
            WorkerResult(i, [value for _, value in chunk], entry_count)
            for i, chunk in enumerate(chunks)
        ]

    monkeypatch.setattr(_processes, "process_pool", lambda _: nullcontext())
    monkeypatch.setattr(_processes, "run_workers", run)
    test_processes.test_process_writes(
        benchmark, tmp_path / "database.json", entries, 1, 2, request
    )
    assert benchmark.extra_info["writes"] == min(100, entry_count)
    assert benchmark.extra_info["flush_every"] == 1
    assert benchmark.extra_info["correctness"] == "passed"


@pytest.mark.parametrize(
    ("bad_call", "disabled"), [(1, False), (2, False), (3, False), (1, True)]
)
def test_every_flush_round_requires_a_write(tmp_path, monkeypatch, bad_call, disabled):
    path = tmp_path / "benchmark.json"
    entries = make_entries(100, 32)
    write_database(path, entries)
    cache = load_cache(str(path))
    original = cache.flush
    calls = 0

    def sometimes_noop():
        nonlocal calls
        calls += 1
        if calls != bad_call:
            original()

    monkeypatch.setattr(cache, "flush", sometimes_noop)
    with pytest.raises(AssertionError):
        test_persistence.test_flush(Rounds(disabled), cache, path, entries, 3)
    assert calls == bad_call
