from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Query

from .cache import Cache, flush, load
from .config import DB_FILE
from .db import delete, insert, select

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load(DB_FILE, cache)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    return cache


@app.put("/db")
def put(
    key: str,
    value: str,
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
    ttl: float | None = Query(default=None, gt=0, description="Time-to-live in seconds"),
):
    insert(key, value, cache, ttl)
    background_tasks.add_task(flush, cache)
    return value


@app.get("/db")
def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return select(key, cache)


@app.delete("/db")
def remove(
    key: str,
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
):
    delete(key, cache)
    background_tasks.add_task(flush, cache)
    return {"deleted": key}
