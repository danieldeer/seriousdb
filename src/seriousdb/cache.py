"""In-memory key-value cache backed by a JSON file and a write-ahead log.

The whole database is held in memory as a ``dict``. Writes are durably
appended to a :class:`~seriousdb.wal.WriteAheadLog` before returning, and periodically
compacted into the full JSON snapshot file (see :data:`COMPACTION_THRESHOLD`).
All access to the data is guarded by a thread lock. File changes also hold a
sidecar lock shared by processes using the same database path.
"""

import logging
from collections.abc import Iterable
from threading import Lock

from .exceptions import ResourceNotFoundError, ServiceUnavailableError
from .persistence import (
    COMPACTION_THRESHOLD,  # noqa: F401 (compatibility export)
    Persistence,
)
from .wal import DeleteEntry, SetEntry, WriteAheadLog

logger = logging.getLogger(__name__)


class Cache:
    """Thread-safe in-memory key-value store persisted to a JSON file.

    A new cache holds no data. Call :meth:`load` before using it; until then
    every data access raises
    :class:`~seriousdb.exceptions.ServiceUnavailableError`.
    Writes refresh the snapshot and WAL under a process lock. Reads may retain
    an older in-memory view until this cache writes or loads again.

    Attributes
    ----------
    filename : str or None
        Path of the database file, or ``None`` if nothing has been loaded.
    wal: WriteAheadLog or None
        The write-ahead log backing this cache, or `None` if nothing has been loaded.
    db : dict of str to str or None
        The stored key-value pairs, or ``None`` if nothing has been loaded.
    lock : threading.Lock
        Lock that must be held while reading or changing `db`.
    """

    def __init__(self):
        self.filename: str | None = None
        self.wal: WriteAheadLog | None = None
        self.db: dict[str, str] | None = None
        self.lock = Lock()
        self._persistence: Persistence | None = None

    def insert(self, key: str, value: str) -> tuple[str, bool]:
        """Store `value` under `key`, replacing any existing value.

        The change is appended to the write-ahead log (WAL) and must succeed there before
        it is applied in memory, so a failed write never leaves the live cache disagreeing
        with what is durable. The full database snapshot file is only rewritten periodically,
        by the persistence layer.

        Parameters
        ----------
        key : str
            Key to store the value under.
        value : str
            Value to store.

        Returns
        -------
        value : str
            The stored value.
        is_new_key : bool
            ``True`` if `key` did not exist before, ``False`` if an existing
            value was replaced.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        OSError
            If the write-ahead log cannot be written. `self.db` is left unchanged in this case.
        """
        with self.lock:
            persistence = _require_persistence(self)
            with persistence.write_state(require_db(self)) as state:
                is_new_key = key not in state.data
                self.db = persistence.persist(state, SetEntry(key=key, value=value))
        return value, is_new_key

    def select(self, key: str) -> str:
        """Return the value stored under `key`.

        Parameters
        ----------
        key : str
            Key to look up.

        Returns
        -------
        str
            The value stored under `key`.

        Raises
        ------
        ResourceNotFoundError
            If `key` does not exist.
        ServiceUnavailableError
            If no database has been loaded.
        """
        with self.lock:
            val = require_db(self).get(key, None)
        if val is None:
            logger.debug("Key not found: %s", key)
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def delete(self, key: str) -> str:
        """Remove `key` and return the value it had.

        If `key` exists, its removal is appended to the write-ahead log (WAL) and
        must succeed there before it is applied in memory, so a failed write never
        leaves the live cache disagreeing with what is durable.


        Parameters
        ----------
        key : str
            Key to remove.

        Returns
        -------
        str
            The value `key` had before it was removed.

        Raises
        ------
        ResourceNotFoundError
            If `key` does not exist.
        ServiceUnavailableError
            If no database has been loaded.
        OSError
            If the write-ahead log cannot be written. `self.db` is left unchanged in this case.
        """
        with self.lock:
            persistence = _require_persistence(self)
            with persistence.write_state(require_db(self)) as state:
                val = state.data.get(key, None)
                if val is not None:
                    self.db = persistence.persist(state, DeleteEntry(key=key))
        if val is None:
            logger.debug("Key not found: %s", key)
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def exists(self, key: str) -> bool:
        """Return whether `key` exists in the database.

        Parameters
        ----------
        key : str
            Key to look up.

        Returns
        -------
        bool
            ``True`` if `key` exists, ``False`` otherwise.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        with self.lock:
            return key in require_db(self)

    def __contains__(self, key: str) -> bool:
        """Return whether `key` exists in the database.

        Parameters
        ----------
        key : str
            Key to look up.

        Returns
        -------
        bool
            ``True`` if `key` exists, ``False`` otherwise.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        return self.exists(key)

    def get_all(self) -> dict[str, str]:
        """Return a snapshot of every key-value pair in the database.

        Returns
        -------
        dict of str to str
            All stored key-value pairs.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        with self.lock:
            return require_db(self).copy()

    def get_bulk(self, keys: Iterable[str]) -> dict[str, str]:
        """Return the values stored under multiple keys.

        Keys that do not exist are omitted from the result.

        Parameters
        ----------
        keys : Iterable of str
            Keys to look up.

        Returns
        -------
        dict of str to str
            A key-value pair for each requested key that exists in the database.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        key_list = tuple(keys)
        with self.lock:
            db = require_db(self)
            return {key: db[key] for key in key_list if key in db}

    def count(self) -> int:
        """Return the number of key-value pairs in the database.

        Returns
        -------
        int
            The number of stored key-value pairs.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        with self.lock:
            return len(require_db(self))

    def __len__(self) -> int:
        """Return the number of key-value pairs in the database.

        Returns
        -------
        int
            The number of stored key-value pairs.

        Raises
        ------
        ServiceUnavailableError
            If no database has been loaded.
        """
        return self.count()

    def load(self, filename: str) -> None:
        """Load the database from `filename`, replacing the current data.

        If the file does not exist, it is created with an empty database.
        If it is not valid UTF-8 JSON or does not contain a JSON object, it is
        renamed to ``<filename>.corrupt-<unix timestamp>``. If that backup already
        exists, a numeric suffix is appended (such as ``-1``, ``-2``, etc) to avoid overwriting it.
        A warning is logged, and a new file with an empty database is created in its
        place.

        After the snapshot is loaded, any entries in the write-ahead log
        (``<filename>.wal``) are replayed on top of it, recovering writes
        that happened after the last compaction.

        Parameters
        ----------
        filename : str
            Path of the database file.

        Raises
        ------
        OSError
            If the file cannot be read, renamed or written.
        """
        with self.lock:
            persistence = Persistence(filename)
            db = persistence.load()
            self.filename = persistence.filename
            self.db, self.wal = db, persistence.wal
            self._persistence = persistence

    def flush(self) -> None:
        """No-op, kept for backward compatibility.

        Durability is now handled per-write via the write-ahead log (see
        :attr:`wal`), so nothing needs to happen here. This method
        exists so that call keeps working without change.
        """
        return


def require_db(cache: Cache) -> dict[str, str]:
    """Return the loaded data of `cache`.

    The caller must hold ``cache.lock`` while using the returned ``dict``.

    Parameters
    ----------
    cache : Cache
        Cache to read the data from.

    Returns
    -------
    dict of str to str
        The loaded key-value pairs. This is the cache's own ``dict``, not a
        copy.

    Raises
    ------
    ServiceUnavailableError
        If `cache` has no database loaded.
    """
    if cache.db is None:
        logger.error("Database unavailable: %s", cache.filename)
        raise ServiceUnavailableError(
            f"Database file {cache.filename} could not be opened and loaded"
        )

    return cache.db


def _require_persistence(cache: Cache) -> Persistence:
    """Return persistence for a loaded cache; the caller must hold its thread lock."""
    require_db(cache)
    if cache._persistence is None:
        raise ServiceUnavailableError("Database file has not been loaded")
    return cache._persistence


def require_wal(cache: Cache) -> WriteAheadLog:
    """Return the write-ahead log of `cache`.

    The caller must hold ``cache.lock`` while using the returned log.

    Parameters
    ----------
    cache : Cache
        Cache to read the write-ahead log from.

    Returns
    -------
    WriteAheadLog
        The cache's write-ahead log.

    Raises
    ------
    ServiceUnavailableError
        If `cache` has no database loaded.
    """
    if cache.wal is None:
        logger.error("Write-ahead log unavailable: %s", cache.filename)
        raise ServiceUnavailableError(
            f"Database file {cache.filename} could not be opened and loaded"
        )

    return cache.wal
