from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI

from .cache import Cache
from .config import DB_FILE

cache = Cache()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Load the on-disk cache into memory for the lifetime of the app."""
    cache.load(DB_FILE)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    """Return the process-wide cache instance."""
    return cache


CacheDep = Annotated[Cache, Depends(get_cache)]


@app.put("/db")
async def put(key: str, value: str, background_tasks: BackgroundTasks, cache: CacheDep) -> str:
    """Store `value` under `key` and persist the cache to disk."""
    cache.insert(key, value)
    background_tasks.add_task(cache.flush)
    return value


@app.get("/db")
async def get(key: str, cache: CacheDep) -> str:
    """Return the value stored under `key`."""
    return cache.select(key)


@app.delete("/db")
async def delete(key: str, cache: CacheDep) -> str:
    """Remove and return the value stored under `key`."""
    return cache.delete(key)
