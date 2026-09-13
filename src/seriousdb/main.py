from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI

from .cache import Cache, flush, load
from .config import DB_FILE
from .db import insert, select

cache = Cache()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Load the on-disk cache into memory for the lifetime of the app."""
    load(DB_FILE, cache)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    """Return the process-wide cache instance."""
    return cache


CacheDep = Annotated[Cache, Depends(get_cache)]


@app.put("/db")
async def put(key: str, value: str, cache: CacheDep) -> str:
    """Store `value` under `key` and persist the cache to disk."""
    insert(key, value, cache)
    flush(cache)
    return value


@app.get("/db")
async def get(key: str, cache: CacheDep) -> str:
    """Return the value stored under `key`."""
    return select(key, cache)
