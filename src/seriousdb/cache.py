"""In-memory key-value cache backed by a JSON file.

The whole database is held in memory as a ``dict`` and written back to disk
with :meth:`Cache.flush`. All access to the data is guarded by a lock, so a
single :class:`Cache` can be shared between request handlers.
"""

import json
import logging
import os
import time
from threading import Lock

from .exceptions import ResourceNotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_DB = {}


class Cache:
    """Thread-safe in-memory key-value store persisted to a JSON file.

    A new cache holds no data. Call :meth:`load` before using it; until then
    every data access raises
    :class:`~seriousdb.exceptions.ServiceUnavailableError`.

    Attributes
    ----------
    filename : str or None
        Path of the database file, or ``None`` if nothing has been loaded.
    db : dict of str to str or None
        The stored key-value pairs, or ``None`` if nothing has been loaded.
    lock : threading.Lock
        Lock that must be held while reading or changing `db`.
    """

    def __init__(self):
        self.filename: str | None = None
        self.db: dict[str, str] | None = None
        self.lock = Lock()

    def insert(self, key: str, value: str) -> tuple[str, bool]:
        """Store `value` under `key`, replacing any existing value.

        The change is only kept in memory; call :meth:`flush` to persist it.

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
        """
        with self.lock:
            db = require_db(self)
            is_new_key = key not in db
            db[key] = value
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
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def delete(self, key: str) -> str:
        """Remove `key` and return the value it had.

        The change is only kept in memory; call :meth:`flush` to persist it.

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
        """
        with self.lock:
            val = require_db(self).pop(key, None)
        if val is None:
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def load(self, filename: str) -> None:
        """Load the database from `filename`, replacing the current data.

        If the file does not exist, it is created with an empty database.
        If it is not valid UTF-8 JSON or does not contain a JSON object, it is
        renamed to ``<filename>.corrupt-<unix timestamp>``, a warning is
        logged, and a new file with an empty database is created in its
        place.

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
            if not os.path.isfile(filename):
                self.db = _write_default(filename)
            else:
                try:
                    with open(filename, "rb") as f:
                        self.db = json.loads(f.read().decode())
                        if not isinstance(self.db, dict):
                            raise TypeError(
                                f"expected dict, got {type(self.db).__name__}"
                            )
                except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as e:
                    backup = f"{filename}.corrupt-{int(time.time())}"
                    os.replace(filename, backup)
                    logger.warning(
                        "Corrupt database file %s (%s); moved to %s and starting fresh",
                        filename,
                        e,
                        backup,
                    )
                    self.db = _write_default(filename)
            self.filename = filename

    def flush(self) -> None:
        """Write the current data to the database file.

        The file is overwritten with the full database. Does nothing if no
        database has been loaded.

        Raises
        ------
        OSError
            If the file cannot be written.
        """
        with self.lock:
            if self.db is None or self.filename is None:
                return
            with open(self.filename, "wb+") as f:
                f.write(json.dumps(self.db).encode())


def _write_default(filename: str) -> dict[str, str]:
    with open(filename, "wb") as f:
        f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)


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
        raise ServiceUnavailableError(
            f"Database file {cache.filename} could not be opened and loaded"
        )

    return cache.db
