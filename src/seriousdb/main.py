from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

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
async def put(key: str, value: str, cache: Cache = Depends(get_cache)):
    insert(key, value, cache)
    flush(cache)
    return value


@app.get("/db")
async def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    value = select(key, cache)
    if value is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return value
