"""Spawned workers shared by the process benchmark scenarios."""

import os
from contextlib import contextmanager
from multiprocessing import get_context
from multiprocessing.pool import Pool
from multiprocessing.synchronize import Barrier
from pathlib import Path
from typing import NamedTuple

from seriousdb import api

from ._support import Entries

WORKER_TIMEOUT = 60
_start: Barrier


class WorkerResult(NamedTuple):
    pid: int
    values: list[str]
    key_count: int
    write_error: str | None = None


def _initialize(start: Barrier) -> None:
    global _start
    _start = start


def _worker(filename: str, entries: Entries, mode: str) -> WorkerResult:
    # Preload outside timing for resident reads. For writes, load before the
    # barrier so no writer can race another process's initial file read.
    if mode in ("preload", "write"):
        api.load(filename)
    # One task per process: no worker can finish and take another worker's task
    # while the remaining workers are still starting or loading their caches.
    _start.wait(timeout=WORKER_TIMEOUT / 2)
    if mode in ("ready", "preload"):
        return WorkerResult(os.getpid(), [], 0)
    if mode == "load-and-read":
        api.load(filename)
    else:
        assert mode in ("resident-read", "write")
    write_error = None
    if mode == "write":
        for key, value in entries:
            try:
                api.set(key, value)
            except PermissionError as error:
                # Attempt all assigned API writes, recording recognized Windows
                # replacement conflicts. Unrelated errors still propagate.
                code = getattr(error, "winerror", None)
                if code not in (5, 32, 33) or error.filename2 != filename:
                    raise
                write_error = f"atomic replacement conflict (WinError {code})"
    values = [api.get(key) for key, _ in entries]
    return WorkerResult(os.getpid(), values, api.count(), write_error)


@contextmanager
def process_pool(workers: int):
    """Use spawn on every platform and terminate/join children even on failure."""
    context = get_context("spawn")
    with context.Pool(
        workers, initializer=_initialize, initargs=(context.Barrier(workers),)
    ) as pool:
        yield pool


def run_workers(
    pool: Pool, database_file: Path, chunks: list[Entries], mode: str
) -> list[WorkerResult]:
    """Dispatch one chunk per process and bound the wait for failed workers."""
    return pool.starmap_async(
        _worker,
        [(str(database_file), chunk, mode) for chunk in chunks],
        chunksize=1,
    ).get(timeout=WORKER_TIMEOUT)
