"""Coordinate database file changes between local processes."""

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager

if os.name == "nt":
    import msvcrt
else:
    import fcntl


@contextmanager
def locked_database(filename: str) -> Iterator[None]:
    """Hold an exclusive lock on a stable sidecar file for a database path.

    The lock file is never replaced or removed: locking the snapshot or WAL
    itself would stop protecting the path when compaction replaces those files.
    """
    lock_path = os.path.normcase(os.path.realpath(filename)) + ".lock"
    with open(lock_path, "a+b") as lock_file:
        if os.name == "nt":
            lock_file.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except PermissionError:
                    time.sleep(0.01)
        else:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
