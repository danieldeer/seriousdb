from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query

from .cache import Cache
from .config import DB_FILE, DEFAULT_KEYS_LIMIT, MAX_KEYS_LIMIT

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cache.load(DB_FILE)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    return cache


@app.put("/db")
def put(
    key: Annotated[str, Query(min_length=1)],
    value: str,
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
) -> str:
    cache.insert(key, value)
    background_tasks.add_task(cache.flush)
    return value


@app.get("/db/keys")
def get_keys(
    cache: Annotated[Cache, Depends(get_cache)],
    limit: int = DEFAULT_KEYS_LIMIT,
    cursor: str | None = None,
):
    if not 1 <= limit <= MAX_KEYS_LIMIT:
        raise HTTPException(
            status_code=400, detail=f"limit must be between 1 and {MAX_KEYS_LIMIT}"
        )

    keys, next_cursor = cache.keys(limit=limit, cursor=cursor)
    return {"keys": keys, "next_cursor": next_cursor}


@app.get("/db")
def get(key: str, cache: Annotated[Cache, Depends(get_cache)]) -> str:
    return cache.select(key)


@app.head("/db")
async def head(key: str, cache: Annotated[Cache, Depends(get_cache)]) -> str:
    return cache.select(key)


@app.get("/db/all")
def get_all(cache: Annotated[Cache, Depends(get_cache)]) -> dict[str, str]:
    with cache.lock:
        if cache.db is None:
            raise HTTPException(
                status_code=500,
                detail=f"Database file {cache.filename} could not be opened and loaded",
            )
        return cache.db.copy()


@app.delete("/db")
def delete(key: str, cache: Annotated[Cache, Depends(get_cache)]) -> str:
    return cache.delete(key)
