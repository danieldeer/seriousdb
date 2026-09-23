"""Benchmark-only options, dataset selection, and isolated database fixtures."""

from argparse import ArgumentTypeError
from importlib.metadata import version
from pathlib import Path

import pytest

from ._support import (
    RANDOM_SEED,
    WORKLOAD_VERSION,
    Entries,
    load_cache,
    make_entries,
    write_database,
)

DEFAULT_DATASETS = [(100, 32), (1_000, 32), (1_000, 1_024)]
EXTENDED_DATASETS = [(10_000, 32), (100_000, 32)]


def _positive_int(value: str) -> int:
    """Parse a command-line value that must be at least one."""
    number = int(value)
    if number < 1:
        raise ArgumentTypeError("must be a positive integer")
    return number


def pytest_addoption(parser):
    """Register command-line controls used only by the benchmark suite."""
    group = parser.getgroup("seriousdb benchmarks")
    group.addoption(
        "--extended", action="store_true", help="Add 10k/100k SeriousDB datasets."
    )
    group.addoption(
        "--engine-rounds",
        type=_positive_int,
        default=5,
        help="Measured rounds per scenario (default: 5).",
    )
    group.addoption(
        "--process-counts",
        type=_positive_int,
        nargs="+",
        default=[1, 2, 4, 8],
        help="Process counts for multi-process benchmarks (default: 1 2 4 8).",
    )
    group.addoption(
        "--multiprocess-writes",
        action="store_true",
        help="Include experimental shared-file writes; data loss is an expected failure.",
    )


def pytest_generate_tests(metafunc):
    """Run every benchmark that requests entries against each selected dataset."""
    if "processes" in metafunc.fixturenames:
        metafunc.parametrize(
            "processes",
            metafunc.config.getoption("--process-counts"),
            ids=lambda n: f"{n}-processes",
        )
    if "entries" not in metafunc.fixturenames:
        return
    datasets = DEFAULT_DATASETS.copy()
    if metafunc.config.getoption("--extended"):
        datasets.extend(EXTENDED_DATASETS)

    metafunc.parametrize(
        "entries",
        [
            pytest.param(dataset, id=f"{dataset[0]}x{dataset[1]}B")
            for dataset in datasets
        ],
        indirect=True,
    )


@pytest.fixture
def measured_rounds(request) -> int:
    """Return the requested number of timed samples for each scenario."""
    return request.config.getoption("--engine-rounds")


@pytest.fixture
def entries(request, benchmark) -> Entries:
    """Build one dataset and attach its shape to the saved benchmark result."""
    count, value_bytes = request.param
    benchmark.extra_info.update(
        entries=count,
        value_bytes=value_bytes,
        seed=RANDOM_SEED,
        seriousdb_version=version("seriousdb"),
        workload_version=WORKLOAD_VERSION,
        persistence="none during timed work",
        workers=1,
    )
    return make_entries(count, value_bytes)


@pytest.fixture
def database_file(tmp_path: Path) -> Path:
    """Give each test an isolated database path that pytest removes afterward."""
    return tmp_path / "database.json"


@pytest.fixture
def loaded_cache(database_file: Path, entries: Entries):
    """Provide a populated cache when loading is setup rather than timed work."""
    write_database(database_file, entries)
    return load_cache(str(database_file))
