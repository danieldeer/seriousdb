"""Read-only process scaling and an opt-in concurrent write failure probe."""

import json
from pathlib import Path

import pytest

from . import _processes
from ._support import WARMUP_ROUNDS, Entries


def _verify_reads(
    results: list[_processes.WorkerResult], chunks: list[Entries], key_count: int
) -> None:
    assert len(results) == len(chunks)
    assert len({result.pid for result in results}) == len(chunks)
    assert [result.values for result in results] == [
        [value for _, value in chunk] for chunk in chunks
    ]
    assert all(result.key_count == key_count for result in results)


@pytest.mark.parametrize("mode", ["load-and-read", "resident-read"])
@pytest.mark.benchmark(group="seriousdb-process-reads")
def test_process_reads(
    benchmark,
    database_file: Path,
    entries: Entries,
    measured_rounds: int,
    processes: int,
    mode: str,
) -> None:
    """Measure a fixed total of API key lookups split across spawned processes.

    Each process reads the shared file through independent API state. Time
    api.load in load-and-read mode; preload outside timing in resident-read mode.
    Both include api.get, api.count, synchronization and result communication,
    which can dominate small workloads. Startup and checks of values, counts,
    worker IDs and the unchanged file are untimed. The OS may cache the file.
    """
    # Seed the fixture outside timing without depending on storage internals.
    database_file.write_text(json.dumps(dict(entries)), encoding="utf-8")
    original = database_file.read_bytes()
    chunks = [entries[index::processes] for index in range(processes)]
    results: list[_processes.WorkerResult] = []
    benchmark.extra_info.update(
        workers=processes,
        interface="seriousdb.api",
        concurrency="spawned processes with independent API state, shared file",
        start_method="spawn",
        file_bytes=len(original),
        reads=len(entries),
        loads_per_round=processes if mode == "load-and-read" else 0,
        workload="fixed total reads split across processes",
        cache_state="api.load each round" if mode == "load-and-read" else "resident",
        timing="dispatch, synchronization, API operations and result IPC; excludes startup",
    )

    with _processes.process_pool(processes) as pool:
        # Wait for every child to start (and optionally load) outside timing.
        _processes.run_workers(
            pool,
            database_file,
            chunks,
            "preload" if mode == "resident-read" else "ready",
        )

        def read():
            nonlocal results
            results = _processes.run_workers(pool, database_file, chunks, mode)

        def verify():
            _verify_reads(results, chunks, len(entries))
            assert database_file.read_bytes() == original

        benchmark.pedantic(
            read,
            teardown=verify,
            rounds=measured_rounds,
            warmup_rounds=WARMUP_ROUNDS,
        )
        # --benchmark-disable skips teardown.
        verify()


@pytest.mark.benchmark(group="seriousdb-process-writes-experimental")
def test_process_writes(
    benchmark,
    database_file: Path,
    entries: Entries,
    measured_rounds: int,
    processes: int,
    request,
) -> None:
    """Probe unsupported concurrent API writes to a shared temporary file.

    With --multiprocess-writes, split up to 100 disjoint updates across processes.
    Time API loading, synchronization, api.set (persisting each write), local
    readback, counts and result communication. Startup, fixture resets and raw
    JSON verification are untimed. A single writer must pass; known concurrent
    persistence failures produce XFAIL and failure metadata. Failed timings are
    not valid throughput, and passing rounds do not establish process safety.
    """
    if not request.config.getoption("--multiprocess-writes"):
        pytest.skip(
            "opt in with --multiprocess-writes; concurrent writes may lose data"
        )

    # Each API set persists the whole file; bound writes for the extended datasets.
    updates = tuple((key, value[::-1]) for key, value in entries[:100])
    expected = dict(entries)
    expected.update(updates)
    chunks = [updates[index::processes] for index in range(processes)]
    results: list[_processes.WorkerResult] = []
    failures: list[str] = []
    benchmark.extra_info.update(
        workers=processes,
        interface="seriousdb.api",
        concurrency="experimental shared-file writes from independent processes",
        start_method="spawn",
        writes=len(updates),
        flush_every=1,
        persistence="api.set persists each write; concurrent writes unsupported",
        timing="API load, synchronize, set, get, count and result IPC; excludes startup",
    )

    with _processes.process_pool(processes) as pool:
        _processes.run_workers(pool, database_file, chunks, "ready")

        def restore():
            # Replace directly: never load or repair a previous corrupt result.
            database_file.write_text(json.dumps(dict(entries)), encoding="utf-8")

        def write():
            nonlocal results
            results = _processes.run_workers(pool, database_file, chunks, "write")

        def verify():
            _verify_reads(results, chunks, len(entries))
            # Inspect raw JSON so Cache.load cannot hide corruption by repairing it.
            write_errors = [
                result.write_error for result in results if result.write_error
            ]
            if write_errors:
                if processes == 1:
                    pytest.fail(
                        "Single-process write failed: " + "; ".join(write_errors)
                    )
                failures.extend(write_errors)
            try:
                persisted = json.loads(database_file.read_bytes())
            except (ValueError, UnicodeDecodeError):
                failure = "invalid persisted JSON"
            else:
                failure = (
                    "lost or incorrect persisted updates"
                    if persisted != expected
                    else ""
                )
            if failure:
                if processes == 1:
                    pytest.fail(f"Single-process write failed: {failure}")
                failures.append(failure)

        benchmark.pedantic(
            write,
            setup=restore,
            teardown=verify,
            rounds=measured_rounds,
            warmup_rounds=WARMUP_ROUNDS,
        )
        verify()

    benchmark.extra_info.update(
        correctness="failed" if failures else "passed",
        persistence_failures=sorted(set(failures)),
        file_bytes=database_file.stat().st_size,
    )
    if failures:
        pytest.xfail(
            "Concurrent writes are unsupported: " + "; ".join(sorted(set(failures)))
        )
