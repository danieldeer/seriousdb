"""Raw fixed-size page I/O on the ``.sdb`` database file."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Self

from .exceptions import DiskManagerError
from .storage_format import PAGE_SIZE
from .types import UInt32

__all__ = ["DiskManager"]

# os.pread/os.pwrite do not exist on Windows. Looked up with getattr so that
# type checkers do not depend on the platform they run on.
_pread = getattr(os, "pread", None)
_pwrite = getattr(os, "pwrite", None)
# Windows only: stops newline translation.
_O_BINARY = getattr(os, "O_BINARY", 0)


class DiskManager:
    """Read and write fixed-size pages of the database file by page ID.

    Page n is stored at byte offset n * PAGE_SIZE. This class does raw
    page I/O only: it knows nothing about page contents, and locking is left
    to the concurrency manager.

    Parameters
    ----------
    path : str or Path
        Database file, created if missing.
    repair_torn_page : bool, optional
        Truncate a partial last page instead of raising. Default False.

    Raises
    ------
    DiskManagerError
        If the file size is not a multiple of PAGE_SIZE and
        repair_torn_page is false.
    OSError
        If the file cannot be opened.

    Notes
    -----
    A new file is empty, so the first :meth:allocate_page returns 0 and the
    caller must write the metadata page there.
    """

    def __init__(self, path: str | Path, *, repair_torn_page: bool = False) -> None:
        self._path = Path(path)
        self._lock = RLock()
        self._fd: int | None = None
        self._known_pages = 0
        self._active = 0  # I/O calls currently using the fd
        fd = os.open(self._path, os.O_RDWR | os.O_CREAT | _O_BINARY, 0o644)
        try:
            size = os.fstat(fd).st_size
            tail = size % PAGE_SIZE
            if tail:
                if not repair_torn_page:
                    raise DiskManagerError(
                        f"{self._path} is {size} bytes, not a multiple of "
                        f"{PAGE_SIZE}; the last page is incomplete"
                    )
                size -= tail
                os.ftruncate(fd, size)
                os.fsync(fd)
            self._known_pages = size // PAGE_SIZE
        except BaseException:
            os.close(fd)
            raise
        self._fd = fd

    @property
    def path(self) -> Path:
        """Path of the database file."""
        return self._path

    @property
    def page_count(self) -> int:
        """Number of whole pages in the file, read from the file size."""
        with self._in_flight() as fd:
            return self._refresh_page_count(fd)

    def read_page(self, page_id: UInt32) -> bytes:
        """Return the PAGE_SIZE`` bytes of page page_id.

        Raises
        ------
        DiskManagerError
            If page_id is out of range, the file is closed, or the file
            ends before a full page could be read.
        """
        with self._in_flight() as fd:
            offset = self._offset(fd, page_id)
            buf = bytearray()
            while len(buf) < PAGE_SIZE:
                chunk = self._read_at(fd, PAGE_SIZE - len(buf), offset + len(buf))
                if not chunk:
                    raise DiskManagerError(
                        f"unexpected end of file reading page {page_id}"
                    )
                buf += chunk
            return bytes(buf)

    def write_page(self, page_id: UInt32, data: bytes) -> None:
        """Overwrite the existing page page_id with data.

        Not fsynced; call :meth:sync when the write must be durable.

        Raises
        ------
        DiskManagerError
            If data is not exactly PAGE_SIZE bytes, page_id has not
            been allocated, or the file is closed.
        """
        if len(data) != PAGE_SIZE:
            raise DiskManagerError(
                f"page data must be {PAGE_SIZE} bytes, got {len(data)}"
            )
        with self._in_flight() as fd:
            self._write_all(fd, data, self._offset(fd, page_id))

    def allocate_page(self) -> UInt32:
        """Allocate a new page at the end of the file and return its ID.

        The page is zero-filled. Reusing freed pages is the caller's job.
        Not fsynced; call :meth:`sync` before relying on the new size after
        a crash.

        Raises
        ------
        DiskManagerError
            If the file is closed or page IDs would exceed the UInt32 range.
        """
        with self._in_flight() as fd, self._lock:
            count = self._refresh_page_count(fd)
            if count > UInt32.MAX:
                raise DiskManagerError("page ID would exceed the UInt32 range")
            self._write_all(fd, bytes(PAGE_SIZE), count * PAGE_SIZE)
            self._known_pages = count + 1
            return UInt32(count)

    def sync(self) -> None:
        """Flush file contents and size to stable storage (fsync)."""
        with self._in_flight() as fd:
            os.fsync(fd)

    def close(self) -> None:
        """Close the file. Safe to call more than once.

        Raises
        ------
        DiskManagerError
            If a read, write, allocation or sync is still running.
        """
        with self._lock:
            if self._active:
                raise DiskManagerError("cannot close while I/O is in progress")
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None

    def __enter__(self) -> Self:
        """Return the manager for use in a ``with`` block."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the file when leaving the ``with`` block."""
        self.close()

    @contextmanager
    def _in_flight(self) -> Iterator[int]:
        # Counts the call as running so close() cannot free the fd under it.
        with self._lock:
            fd = self._require_open()
            self._active += 1
        try:
            yield fd
        finally:
            with self._lock:
                self._active -= 1

    def _require_open(self) -> int:
        if self._fd is None:
            raise DiskManagerError("the database file is closed")
        return self._fd

    def _refresh_page_count(self, fd: int) -> int:
        count = os.fstat(fd).st_size // PAGE_SIZE
        self._known_pages = max(self._known_pages, count)
        return count

    def _offset(self, fd: int, page_id: UInt32) -> int:
        # The file only grows while open, so the cached count is a lower
        # bound: re-read the file size only when an ID is beyond it, which
        # also picks up pages another handle allocated.
        if page_id >= self._known_pages:
            self._refresh_page_count(fd)
        if not 0 <= page_id < self._known_pages:
            raise DiskManagerError(
                f"page {page_id} is out of range (0..{self._known_pages - 1})"
            )
        return page_id * PAGE_SIZE

    def _read_at(self, fd: int, size: int, offset: int) -> bytes:
        if _pread is not None:
            return _pread(fd, size, offset)
        with self._lock:  # seek + read must be atomic without pread
            os.lseek(fd, offset, os.SEEK_SET)
            return os.read(fd, size)

    def _write_all(self, fd: int, data: bytes, offset: int) -> None:
        view = memoryview(data)
        written = 0
        while written < len(view):
            if _pwrite is not None:
                n = _pwrite(fd, view[written:], offset + written)
            else:
                with self._lock:
                    os.lseek(fd, offset + written, os.SEEK_SET)
                    n = os.write(fd, view[written:])
            if n <= 0:
                raise DiskManagerError("write made no progress")
            written += n
