"""A deterministic read-heavy workload on one loaded cache."""

from pathlib import Path

import pytest

from seriousdb.cache import Cache

from ._support import (
    WARMUP_ROUNDS,
    Entries,
    assert_entries,
    expected_state,
    mixed_operations,
    run_operations,
    verify_persisted,
)


@pytest.mark.benchmark(group="seriousdb-mixed-resident")
def test_mixed_resident(
    benchmark,
    loaded_cache: Cache,
    database_file: Path,
    entries: Entries,
    measured_rounds: int,
) -> None:
    """Measure a shuffled in-memory workload of 90% reads and 10% overwrites.

    Run one operation per entry. Resetting values, checking results and the final
    flush and reopen check are untimed.
    """
    operations = mixed_operations(entries)
    expected = expected_state(entries, operations)
    expected_reads = [value for action, _, value in operations if action == "read"]
    values: list[str] = []

    def run():
        """Execute the whole mixed workload while the timer runs."""
        nonlocal values
        values = run_operations(loaded_cache, operations)

    def restore_entries():
        """Undo prior overwrites before each warmup or measured round."""
        for key, value in entries:
            loaded_cache.insert(key, value)

    def verify():
        """Check read results and final in-memory state after timing stops."""
        assert values == expected_reads
        assert_entries(loaded_cache, expected)

    benchmark.extra_info.update(
        reads=len(expected_reads),
        writes=len(entries) - len(expected_reads),
        persistence="in-memory only",
    )
    # Reset and verification are intentionally outside the timed run callback.
    benchmark.pedantic(
        run,
        setup=restore_entries,
        teardown=verify,
        rounds=measured_rounds,
        warmup_rounds=WARMUP_ROUNDS,
    )
    # Persist once after all samples so this in-memory benchmark also proves that
    # its final state can be written and reopened correctly.
    verify()
    loaded_cache.flush()
    verify_persisted(database_file, expected)
