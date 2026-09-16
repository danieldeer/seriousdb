import time

from fastapi import HTTPException

from .cache import Cache, is_expired


def insert(key: str, value: str, cache: Cache, ttl: float | None = None):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=500,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        cache.db[key] = value
        if ttl is not None:
            cache.ttl[key] = time.time() + ttl
        else:
            cache.ttl.pop(key, None)
    return value


def select(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=500,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        if is_expired(key, cache):
            cache.db.pop(key, None)
            del cache.ttl[key]
            raise HTTPException(status_code=404, detail=f"No value set for key {key}")
        val = cache.db.get(key, None)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val


def delete(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=500,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        cache.db.pop(key, None)
        cache.ttl.pop(key, None)
