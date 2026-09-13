from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from .cache import Cache, load, flush
from .db import insert, select
from .config import DB_FILE

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
async def get(key: str, cache: Cache = Depends(get_cache)):
    return select(key, cache)
