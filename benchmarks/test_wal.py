"""Benchmarks for write-ahead log persistence."""

from pathlib import Path

import pytest

from seriousdb.wal import SetEntry, WriteAheadLog

from ._support import WARMUP_ROUNDS


@pytest.mark.benchmark(group="wal")
def test_wal_append(
    benchmark,
    database_file: Path,
    measured_rounds: int,
) -> None:
    """Measure appending one entry to the WAL, including fsync."""

    entry = SetEntry(key="key", value="value")

    def prepare_wal():
        database_file.unlink(missing_ok=True)
        wal = WriteAheadLog(str(database_file))
        return (wal,), {}

    def append_entry(wal: WriteAheadLog) -> None:
        wal.append(entry)

    def close_wal(wal: WriteAheadLog) -> None:
        wal.close()

    benchmark.extra_info.update(
        operation="WAL append",
        persistence="write + flush + fsync",
        key_bytes=len(entry.key.encode()),
        value_bytes=len(entry.value.encode()),
    )

    benchmark.pedantic(
        append_entry,
        setup=prepare_wal,
        teardown=close_wal,
        rounds=50,
        warmup_rounds=WARMUP_ROUNDS,
    )
