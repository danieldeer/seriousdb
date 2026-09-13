import time

from fastapi import HTTPException

from .cache import Cache


def insert(key: str, value: str, cache: Cache, ttl: float | None = None):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        if ttl is not None:
            cache.db[key] = {"value": value, "expires_at": time.time() + ttl}
        else:
            cache.db[key] = value
    return value


def select(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        val = cache.db.get(key, None)
        if (
            val is not None
            and isinstance(val, dict)
            and "expires_at" in val
            and time.time() >= val["expires_at"]
        ):
            del cache.db[key]
            val = None
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val
