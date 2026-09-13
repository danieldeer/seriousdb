from fastapi import HTTPException

from .cache import Cache


def insert(key: str, value: str, cache: Cache) -> str:
    """Insert `value` under `key` in `cache`'s database and return it."""
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        cache.db[key] = value
    return value


def select(key: str, cache: Cache) -> str:
    """Return the value stored under `key` in `cache`'s database."""
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        val = cache.db.get(key, None)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val
