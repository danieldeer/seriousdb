"""File load and key lookup costs, measured separately and together."""

from pathlib import Path

import pytest

from seriousdb.cache import Cache

from ._support import (
    WARMUP_ROUNDS,
    Entries,
    assert_entries,
    load_and_read,
    load_cache,
    read_resident,
    write_database,
)


@pytest.mark.benchmark(group="load-and-read-by-key")
def test_load_and_read_by_key(
    benchmark,
    database_file: Path,
    entries: Entries,
    measured_rounds: int,
) -> None:
    """Measure loading a fresh Cache and looking up every key.

    File creation and result checks are untimed. The OS may cache the file.
    """
    # File creation belongs to setup, so it happens once before benchmarking.
    write_database(database_file, entries)
    values: list[str] = []
    expected = [value for _, value in entries]

    def read():
        """Load a new Cache from disk and read all keys while the timer runs."""
        nonlocal values
        values = load_and_read(database_file, entries)

    def verify():
        """Check the completed round's read results after the timer stops."""
        assert values == expected

    benchmark.extra_info.update(
        file_bytes=database_file.stat().st_size,
        lookup="native string key",
    )
    # No per-round setup is needed because this benchmark never mutates the file.
    benchmark.pedantic(
        read,
        teardown=verify,
        rounds=measured_rounds,
        warmup_rounds=WARMUP_ROUNDS,
    )
    verify()


@pytest.mark.benchmark(group="seriousdb-load-file")
def test_load_file(
    benchmark,
    loaded_cache: Cache,
    entries: Entries,
    measured_rounds: int,
) -> None:
    """Measure creating a Cache and loading the database file.

    File creation, key lookups and count checks are untimed. The OS may cache
    the file even though each round uses a fresh application cache.
    """
    filename = loaded_cache.filename
    assert filename is not None
    cache: Cache | None = None

    def load():
        """Create a new Cache and load the file while the timer runs."""
        nonlocal cache
        cache = load_cache(filename)

    def verify():
        """Read the loaded cache outside timing to prove deserialization worked."""
        assert cache is not None
        assert_entries(cache, entries)

    benchmark.pedantic(
        load,
        teardown=verify,
        rounds=measured_rounds,
        warmup_rounds=WARMUP_ROUNDS,
    )
    verify()


@pytest.mark.benchmark(group="seriousdb-resident-read")
def test_resident_read(
    benchmark,
    loaded_cache: Cache,
    entries: Entries,
    measured_rounds: int,
) -> None:
    """Measure key lookups from an already loaded Cache.

    File creation, loading and result checks are untimed.
    """
    values: list[str] = []
    expected = [value for _, value in entries]

    def read():
        """Read all requested keys from the existing Cache inside the timer."""
        nonlocal values
        values = read_resident(loaded_cache, entries)

    def verify():
        """Check the completed round's read results after the timer stops."""
        assert values == expected

    benchmark.pedantic(
        read,
        teardown=verify,
        rounds=measured_rounds,
        warmup_rounds=WARMUP_ROUNDS,
    )
    verify()
