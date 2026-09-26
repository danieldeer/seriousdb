"""Coordinate snapshot recovery, WAL writes, and compaction for one database."""

import json
import logging
import os
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from .process_lock import locked_database
from .wal import WalEntry, WriteAheadLog, _sync_parent_directory

logger = logging.getLogger(__name__)

COMPACTION_THRESHOLD = 50


@dataclass
class WriteState:
    """A current database view staged for a write under the process lock.

    Catching up must not replace the cache's view until the WAL append succeeds.
    The entry count and snapshot identity describe this staged view, rather than
    the older view still held by the cache.
    """

    data: dict[str, str]
    entry_count: int
    snapshot_identity: tuple[int, int, int, int]
    persisted: bool = False


class Persistence:
    """Own the disk state and recovery bookkeeping for one cache.

    ``load`` and ``write_state`` acquire the database's process lock. The cache
    must acquire its thread lock first and hold it through the load call or the
    entire ``write_state`` context.
    """

    def __init__(self, filename: str):
        self.filename = os.path.realpath(os.path.abspath(filename))
        self.wal = WriteAheadLog(f"{self.filename}.wal")
        self._snapshot_identity: tuple[int, int, int, int] | None = None
        self._seen_wal_offset = 0
        self._entry_count = 0

    def load(self) -> dict[str, str]:
        """Load the snapshot and replay its WAL while holding the process lock."""
        with locked_database(self.filename):
            state = self._reload_snapshot_and_wal()
            self._remember(state)
            return state.data

    @contextmanager
    def write_state(self, data: dict[str, str]) -> Iterator[WriteState]:
        """Yield the latest view and hold the process lock until context exit.

        The caller must hold its cache's thread lock. Keeping the process lock
        through ``persist`` prevents another writer from changing the recovered
        state between checking a key and appending its update.
        After a persisted write, compaction runs on context exit, once the cache
        has published the new view.
        """
        with locked_database(self.filename):
            state = self._refresh(data)
            yield state
            # Cache publishes the durable view inside this context. Compact
            # afterwards so even an unexpected error leaves data and counters
            # consistent. A missing-key delete has no write to compact.
            if state.persisted:
                self._compact_if_due(state.data)

    def persist(self, state: WriteState, entry: WalEntry) -> dict[str, str]:
        """Append durably and apply the entry to the staged view.

        The caller must remain inside ``write_state`` with its thread lock held.
        No staged data or bookkeeping is published before the append succeeds.
        The returned data must replace the cache's view before context exit.
        """
        self.wal.append(entry)
        entry.apply(state.data)
        state.entry_count += 1
        self._remember(state)
        state.persisted = True
        return state.data

    def _refresh(self, data: dict[str, str]) -> WriteState:
        """Choose full recovery, WAL catch-up, or the unchanged local view.

        The caller must hold the process lock.
        """
        identity = _snapshot_identity(self.filename)
        wal_size = (
            os.path.getsize(self.wal.filename)
            if os.path.isfile(self.wal.filename)
            else 0
        )

        # Compaction replaces the snapshot and empties the WAL. The old local
        # view cannot recover from the remaining WAL alone, so reload both files.
        if identity != self._snapshot_identity or wal_size < self._seen_wal_offset:
            return self._reload_snapshot_and_wal()

        if wal_size > self._seen_wal_offset:
            return self._replay_new_entries(data, identity)

        # Avoid reading or copying the database when no other writer changed it.
        return WriteState(data, self._entry_count, identity)

    def _reload_snapshot_and_wal(self) -> WriteState:
        """Load the snapshot, repair/replay the WAL, and return recovered state.

        The caller must hold the process lock. Reapplying entries after an
        interrupted compaction is safe because set/delete entries are idempotent.
        """
        data = _load_snapshot(self.filename)
        entries = self.wal.replay()
        for entry in entries:
            entry.apply(data)
        return WriteState(data, len(entries), _snapshot_identity(self.filename))

    def _replay_new_entries(
        self, data: dict[str, str], identity: tuple[int, int, int, int]
    ) -> WriteState:
        """Apply unseen WAL entries to a copy while the process lock is held."""
        entries = self.wal.replay()
        # Replay may repair a corrupt tail. If it removed entries already in our
        # view, rebuild from the snapshot instead of retaining those stale values.
        if len(entries) < self._entry_count:
            return self._reload_snapshot_and_wal()

        refreshed = data.copy()
        for entry in entries[self._entry_count :]:
            entry.apply(refreshed)
        return WriteState(refreshed, len(entries), identity)

    def _remember(self, state: WriteState) -> None:
        """Record which snapshot and WAL entries the published view contains."""
        self._snapshot_identity = state.snapshot_identity
        self._entry_count = state.entry_count
        self._seen_wal_offset = self.wal._offset

    def _compact_if_due(self, data: dict[str, str]) -> None:
        """Keep compaction errors from failing an already durable write.

        The caller must hold the process lock.
        """
        try:
            if self._entry_count >= COMPACTION_THRESHOLD:
                self._compact(data)
        except OSError as error:
            logger.error(
                "Compaction failed after durable write to %s: %s", self.filename, error
            )

    def _compact(self, data: dict[str, str]) -> None:
        """Persist the snapshot before clearing its WAL.

        The caller must hold the process lock. If snapshot persistence fails,
        the WAL stays intact. If clearing the WAL fails, the synced snapshot
        remains the recovery base; replaying any leftover WAL entries is safe.
        """
        _atomic_write_json(self.filename, data)
        logger.info("Compacted database into %s", self.filename)
        self.wal.clear()
        self._entry_count = 0
        self._snapshot_identity = _snapshot_identity(self.filename)
        self._seen_wal_offset = 0


def _load_snapshot(filename: str) -> dict[str, str]:
    """Read the JSON snapshot, creating or replacing it if missing or corrupt.

    The caller must hold the process lock. This function does not replay the WAL.
    Corrupt snapshots are backed up before an empty snapshot is created.
    """
    if not os.path.isfile(filename):
        logger.info(
            "Database file %s does not exist; creating a new database", filename
        )
        _atomic_write_json(filename, {})
        return {}

    try:
        with open(filename, "rb") as file:
            data = json.loads(file.read().decode())
        if not isinstance(data, dict):
            raise TypeError(f"expected dict, got {type(data).__name__}")
        logger.info("Loaded database from %s", filename)
        return data
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        backup = _generate_corrupt_backup_path(filename)
        os.replace(filename, backup)
        logger.warning(
            "Corrupt database file %s (%s); moved to %s and starting fresh",
            filename,
            error,
            backup,
        )
        _atomic_write_json(filename, {})
        return {}


def _atomic_write_json(filename: str, data: dict[str, str]) -> None:
    """Write and sync a temporary snapshot before replacing the destination.

    The caller must hold the process lock. Syncing the parent directory confirms
    the replacement before compaction can safely clear the WAL on POSIX systems.
    Temporary files are cleaned up if writing or replacement fails.
    """
    dir_name = os.path.dirname(filename) or "."
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=dir_name, delete=False) as tmp_file:
            temp_name = tmp_file.name
            tmp_file.write(json.dumps(data).encode())
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(temp_name, filename)
        _sync_parent_directory(filename)
    except Exception:
        if temp_name is not None and os.path.lexists(temp_name):
            os.unlink(temp_name)
        raise


def _snapshot_identity(filename: str) -> tuple[int, int, int, int]:
    """Identify snapshot replacements using file identity, size, and timestamp."""
    stat = os.stat(filename)
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _generate_corrupt_backup_path(filename: str) -> str:
    """Find a free timestamped backup path without overwriting prior backups."""
    base = f"{filename}.corrupt-{int(time.time())}"
    if not os.path.lexists(base):
        return base
    counter = 1
    while os.path.lexists(f"{base}-{counter}"):
        counter += 1
    return f"{base}-{counter}"
