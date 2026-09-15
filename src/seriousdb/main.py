from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query

from .cache import Cache, require_db
from .config import DB_FILE
from .error_handlers import register_exception_handlers

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cache.load(DB_FILE)
    yield


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


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
        return require_db(cache).copy()


@app.delete("/db")
def delete(
    key: str,
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
):
    value = cache.delete(key)
    background_tasks.add_task(cache.flush)
    return value


@app.get("/health")
def health(cache: Annotated[Cache, Depends(get_cache)]):
    if cache.db is None:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return {"status": "ok"}
