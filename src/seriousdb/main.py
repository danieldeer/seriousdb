from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query

from .cache import Cache, flush, load
from .config import DB_FILE
from .db import insert, select

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load(DB_FILE, cache)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    return cache


@app.put("/db")
async def put(
    key: str,
    value: str,
    cache: Annotated[Cache, Depends(get_cache)],
    ttl: float | None = Query(default=None, gt=0),
):
    insert(key, value, cache, ttl=ttl)
    flush(cache)
    return value


@app.get("/db")
async def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return select(key, cache)
