"""Synchronous Python API of seriousdb.

This module is the storage layer of seriousdb: other Python projects can
import the package and call the functions exported here directly.

All functions are thread-safe.
"""

from collections.abc import Iterable
from pathlib import Path
from threading import Lock, Timer

from .cache import Cache, require_db
from .common import _validate_ttl
from .config import DB_FILE

__all__ = [
    "count",
    "delete",
    "exists",
    "get",
    "get_all",
    "get_bulk",
    "set",
]

cache = Cache()

_init_lock = Lock()


def load(filename: str | Path = DB_FILE) -> None:
    """Load the database from `filename`, replacing the current data.

    If the file does not exist, it is created with an empty database.
    If it is not valid UTF-8 JSON or does not contain a JSON object, it is
    renamed to ``<filename>.corrupt-<unix timestamp>`` (with a numeric suffix
    if that path already exists) and replaced with an empty database.

    Parameters
    ----------
    filename : str or Path, optional Path of the database file.
        Default to :data:`~seriousdb.config.DB_FILE`.

    Raises
    ------
    OSError
        if the file cannot be read, renamed or written.
    """
    cache.load(str(filename))


def is_loaded() -> bool:
    """Return whether a database has been loaded.

    Returns
    -------
    bool
        ``True`` if a database file has been loaded,
        ``False`` otherwise.
    """
    return cache.db is not None


def _ensure_loaded() -> None:
    """Load the default database file if nothing has been loaded yet."""
    if is_loaded():
        return
    with _init_lock:
        if not is_loaded():
            load()


def get(key: str) -> str:
    """Return the value stored under `key`.

    the database file is loaded automatically on first use.

    Parameters
    ----------
    key: str
        Key to look up.

    Returns
    -------
    str
        The value stored under `key`.

    Raises
    ------
    ResourceNotFoundError
        If `key` does not exist.
    OSError
        If the database file cannont be loaded.
    """
    _ensure_loaded()
    return cache.select(key)


def set(key: str, value: str, ex: float | None = None) -> str:
    """Store `value` under `key`, overwriting any existing value.

    The change is flushed to the database file before the function returns.

    Parameters
    ----------
    key: str
        Key to store the value under.
    value: str
        Value to store
    ex: float | None
        Time-to-live (TTL) in seconds. If None, the key does not expire.

    Returns
    -------
    str
        The stored value.

    Raises
    ------
    OSError
        If the database file cannont be loaded or written.
    """
    _validate_ttl(ex)
    _ensure_loaded()
    value, _ = cache.insert(key, value)
    cache.flush()

    if ex:
        timer = Timer(ex, delete, [key])
        timer.daemon = True
        timer.start()

    return value


def delete(key: str) -> str:
    """Remove `key` and return the value it had.

    The change is flushed to the database file before the function returns.

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
    _ensure_loaded()
    value = cache.delete(key)
    cache.flush()
    return value


def exists(key: str) -> bool:
    """Return whether `key` exists in the database.

    the database file is loaded automatically on first use.

    Parameters
    ----------
    key : str
        Key to remove.

    Returns
    -------
    bool
        ``True`` if key exists, ``False`` otherwise.
    """
    _ensure_loaded()
    with cache.lock:
        return key in require_db(cache)


def get_all() -> dict[str, str]:
    """Return a snapshot of every key-value pair in the database.

    the database file is loaded automatically on first use.

    Returns
    -------
    dict of str to str
        All stored key-value pairs.

    Raises
    ------
    OSError
        If the database file cannont be loaded.
    """
    _ensure_loaded()
    with cache.lock:
        return require_db(cache).copy()


def get_bulk(keys: Iterable[str]) -> dict[str, str]:
    """Return the values stored under multiple keys.

    Keys that do not exist are omitted from the result.
    the database file is loaded automatically on first use.

    Parameters
    ----------
    keys: Iterable of str
        Keys to lookup.

    Returns
    -------
    dict of str to str
        A key-value pair for each requested key that exists in the database.

    Raises
    ------
    OSError
        If the database file cannont be loaded.
    """
    _ensure_loaded()
    with cache.lock:
        db = require_db(cache)
        return {key: db[key] for key in keys if key in db}


def count() -> int:
    """Return the number of key-value pairs int the database.

    the database file is loaded automatically on first use.

    Returns
    -------
    int
        The number of stored key-value pairs

    Raises
    ------
    OSError
        If the database file cannont be loaded.
    """
    _ensure_loaded()
    with cache.lock:
        return len(require_db(cache))
