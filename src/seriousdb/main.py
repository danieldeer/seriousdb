from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query

from .cache import Cache
from .config import DB_FILE

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


@app.delete("/db", status_code=204)
def delete(key: str, cache: Annotated[Cache, Depends(get_cache)]) -> str:
    return cache.delete(key)
