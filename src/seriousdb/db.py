from fastapi import HTTPException

from .cache import Cache


def insert(key: str, value: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
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
    return val
