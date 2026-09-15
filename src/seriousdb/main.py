from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import JSONResponse

from .cache import Cache
from .config import DB_FILE

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.load(DB_FILE)
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
):
    created = cache.insert(key, value)
    background_tasks.add_task(cache.flush)
    return JSONResponse(status_code=201 if created else 200, content=value)


@app.get("/db")
def get(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return cache.select(key)


@app.delete("/db")
def delete(key: str, cache: Annotated[Cache, Depends(get_cache)]):
    return cache.delete(key)
