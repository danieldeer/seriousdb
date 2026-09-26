"""Append-only write-ahead log for durable, incremental persistence."""

import json
import logging
import os
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class WalEntry:
    """Base class for a single write-ahead log entry.

    Subclasses know how to serialize themselves for storage and how to
    apply themselves to an in-memory database dict.
    """

    def to_dict(self) -> dict:
        """Return the JSON-serializable representation of this entry."""
        raise NotImplementedError

    def apply(self, db: dict[str, str]) -> None:
        """Apply this entry's effect to `db`."""
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> "WalEntry":
        """Reconstruct a `WalEntry` from its serialized form.

        Raises
        ------
        ValueError
            If `data` does not describe a know entry type.
        """
        op = data.get("op")
        if op == "set":
            return SetEntry(key=data["key"], value=data["value"])
        if op == "delete":
            return DeleteEntry(key=data["key"])
        raise ValueError


@dataclass(frozen=True)
class SetEntry(WalEntry):
    """A write-ahead log entry recording that `key` was set to `value`."""

    key: str
    value: str

    def to_dict(self) -> dict:
        """Return the JSON-serializable representation of this entry."""
        return {"op": "set", "key": self.key, "value": self.value}

    def apply(self, db: dict[str, str]) -> None:
        """Apply this entry's effect to `db`."""
        db[self.key] = self.value


@dataclass(frozen=True)
class DeleteEntry(WalEntry):
    """A write-ahead log entry recording that `key` was deleted."""

    key: str

    def to_dict(self) -> dict:
        """Return the JSON-serializable representation of this entry."""
        return {"op": "delete", "key": self.key}

    def apply(self, db: dict[str, str]) -> None:
        """Apply this entry's effect to `db`."""
        db.pop(self.key, None)


class WriteAheadLog:
    """An append-only, crash-safe log of write-ahead log entries.

    Each entry is appended as one JSON-encoded line, flushed and fsynced
    before :meth:`append` returns, so an entry is durable the moment the
    call succeeds. :meth:`replay` reads back every entry that was safely
    written, repairing the file on disk if the last entry was left
    incomplete by a crash mid-write. :meth:`append` also repairs any
    leftover bytes from a previous failed write before writing, so a torn
    write can't corrupt a later append even without a restart.

    Attributes
    ----------
    filename : str
        Path of the log file.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self._offset = os.path.getsize(filename) if os.path.isfile(filename) else 0

    def append(self, entry: WalEntry) -> None:
        """Append `entry` to the log and fsync it.

        Parameters
        ----------
        entry : WalEntry
            The entry to append.

        Raises
        ------
        OSError
            If the log file cannot be written.
        """
        self._repair_torn_tail()
        with open(self.filename, "ab") as f:
            if self._offset == 0:
                _sync_parent_directory(self.filename)
            data = (json.dumps(entry.to_dict()) + "\n").encode()
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        self._offset += len(data)

    def replay(self) -> list[WalEntry]:
        """Return every entry durably written to the log, oldest first.

        Only complete, newline-terminated entries are trusted, an entry
        cut short by a crash mid-write has no way to prove it was fully
        flushed to disk, since :meth:`append` always writes an entry and
        its trailing newline in a single write. If the log ends with an
        entry that is not newline-terminated or does not parse, it is
        dropped, and the file is truncated on disk to just after the last
        trusted entry.

        Returns
        -------
        list of WalEntry
            The decoded entries, in the order they were appended. Empty if
            the log file does not exist yet.
        """
        if not os.path.isfile(self.filename):
            self._offset = 0
            return []

        entries: list[WalEntry] = []
        good_offset = 0
        found_bad_entry = False
        with open(self.filename, "rb") as f:
            for raw_line in f:
                if not raw_line.endswith(b"\n"):
                    found_bad_entry = True
                    break
                line = raw_line.strip()
                if line:
                    try:
                        entries.append(WalEntry.from_dict(json.loads(line.decode())))
                    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
                        logger.warning(
                            "Corrupt entry in write-ahead log %s (%s)",
                            self.filename,
                            e,
                        )
                        found_bad_entry = True
                        break
                good_offset += len(raw_line)

        if found_bad_entry:
            logger.warning(
                "Truncating write-ahead log %s to its last known-good entry",
                self.filename,
            )
            with open(self.filename, "r+b") as f:
                f.truncate(good_offset)

        self._offset = good_offset
        return entries

    def clear(self) -> None:
        """Atomically replace the log with an empty file.

        Raises
        ------
        OSError
            If the temporary or final files cannot be written.
        """
        dir_name = os.path.dirname(self.filename) or "."
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(
                "wb", dir=dir_name, delete=False
            ) as tmp_file:
                temp_name = tmp_file.name
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(temp_name, self.filename)
        except Exception:
            if temp_name is not None and os.path.lexists(temp_name):
                os.unlink(temp_name)
            raise
        self._offset = 0
        _sync_parent_directory(self.filename)

    def _repair_torn_tail(self) -> None:
        """Truncate any bytes left by a previous failed write.

        A prior `append()` call may have written partial bytes before
        raising, leaving the file longer than the last completed entry.
        Repairing here, before the next append, prevents new entries from
        being concatenated onto that leftover, not just after a crash and restart,
        but during long-running process too.
        """
        if not os.path.isfile(self.filename):
            self._offset = 0
            return
        actual_size = os.path.getsize(self.filename)
        if actual_size > self._offset:
            with open(self.filename, "r+b") as f:
                f.truncate(self._offset)


def _sync_parent_directory(filename: str) -> None:
    """Persist a created or replaced file's directory entry on POSIX."""
    if os.name == "nt":
        return
    dir_name = os.path.dirname(filename) or "."
    fd = os.open(dir_name, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
