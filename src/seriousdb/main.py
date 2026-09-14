from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI

from .cache import Cache, flush, load
from .config import DB_FILE
from .db import insert, select

from pydantic import BaseModel, Field


class Entry(BaseModel):
    key: str = Field(min_length=1, description="The key of the entry")
    value: str = Field(description="The value of the entry")


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
    entry: Entry,
    cache: Annotated[Cache, Depends(get_cache)],
    background_tasks: BackgroundTasks,
):
    insert(entry.key, entry.value, cache)
    flush(cache)
    background_tasks.add_task(flush, cache)
    return {"key": entry.key, "value": entry.value}


@app.get("/db")
def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return select(key, cache)
