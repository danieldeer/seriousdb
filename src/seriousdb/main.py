from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Query

from .cache import Cache
from .config import DB_FILE
from .schemas import KeyQuery, KeyRequest

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.load(DB_FILE)
    yield


app = FastAPI(lifespan=lifespan)


def get_cache() -> Cache:
    return cache


@app.put("/db", response_model=str)
def put(
    params: Annotated[KeyRequest, Query()],
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
):
    cache.insert(params.key, params.value)
    background_tasks.add_task(cache.flush)
    return params.value


@app.get("/db", response_model=str)
def get(params: Annotated[KeyQuery, Query()], cache: Annotated[Cache, Depends(get_cache)]):
    return cache.select(params.key)


@app.delete("/db", response_model=str)
def delete(params: Annotated[KeyQuery, Query()], cache: Annotated[Cache, Depends(get_cache)]):
    return cache.delete(params.key)
