from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Body, Depends, FastAPI

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
def put(
    key: str,
    value: Annotated[str, Body(embed=True)],
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
):
    insert(key, value, cache)
    background_tasks.add_task(flush, cache)
    return value


@app.get("/db")
def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return select(key, cache)
