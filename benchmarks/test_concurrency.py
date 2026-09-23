"""Thread contention on a shared cache; these are not process-safety tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from seriousdb.cache import Cache

from ._support import (
    WARMUP_ROUNDS,
    Entries,
    Operations,
    assert_entries,
    expected_state,
    mixed_operations,
    run_operations,
    verify_persisted,
)


@pytest.mark.parametrize("workers", [1, 2, 4, 8], ids=lambda n: f"{n}-threads")
@pytest.mark.benchmark(group="seriousdb-shared-cache-threads")
def test_shared_cache_threads(
    benchmark,
    loaded_cache: Cache,
    database_file: Path,
    entries: Entries,
    measured_rounds: int,
    workers: int,
) -> None:
    """Measure scheduling and contention on a Cache shared by threads.

    Split a fixed workload of 90% reads and 10% overwrites across threads. Timing
    includes submission, synchronization and waiting for results; threads start
    during warmup. Resets, result checks and the final persistence check are untimed.
    """
    # Slicing distributes every nth operation to a worker without duplicating work.
    operations = mixed_operations(entries)
    chunks = [operations[index::workers] for index in range(workers)]
    expected = expected_state(entries, operations)
    expected_reads = [
        [value for action, _, value in chunk if action == "read"] for chunk in chunks
    ]
    start = Barrier(workers, timeout=30)
    values: list[list[str]] = []

    def worker(chunk: Operations):
        """Wait for every worker, then run this worker's share of operations."""
        start.wait()
        return run_operations(loaded_cache, chunk)

    def restore_entries():
        """Undo prior overwrites before each warmup or measured round."""
        for key, value in entries:
            loaded_cache.insert(key, value)

    def verify():
        """Check each worker's reads and the shared cache after timing stops."""
        assert values == expected_reads
        assert_entries(loaded_cache, expected)

    benchmark.extra_info.update(
        workers=workers,
        concurrency="threads sharing one Cache",
        reads=sum(map(len, expected_reads)),
        writes=len(entries) // 10,
        persistence="in-memory only; final flush outside timing",
    )
    # Pool startup is excluded so the samples focus on scheduling work and on
    # contention inside one shared Cache rather than thread construction.
    with ThreadPoolExecutor(max_workers=workers) as executor:

        def run_threads():
            """Submit all chunks, wait for completion, and collect read results."""
            nonlocal values
            futures = [executor.submit(worker, chunk) for chunk in chunks]
            values = [future.result(timeout=60) for future in futures]

        benchmark.pedantic(
            run_threads,
            setup=restore_entries,
            teardown=verify,
            rounds=measured_rounds,
            warmup_rounds=WARMUP_ROUNDS,
        )
    # Submission, barrier synchronization, and joins happen in run_threads, so
    # they are included in each sample. Reset and verification stay outside it.
    verify()
    loaded_cache.flush()
    verify_persisted(database_file, expected)
