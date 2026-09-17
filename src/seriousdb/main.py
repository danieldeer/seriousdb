import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from inspect import cleandoc
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    status,
)

from .cache import Cache, JsonValue, require_db
from .config import DB_FILE, LOG_LEVEL
from .error_handlers import register_exception_handlers
from .parser import parse_value

cache = Cache()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.basicConfig(level=LOG_LEVEL.upper())
    cache.load(DB_FILE)
    yield


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


def get_cache() -> Cache:
    return cache


@app.put(
    "/db",
    response_model=None,
    summary="Store a key-value pair",
    description=cleandoc(
        """
        Stores `value` under `key`, overwriting any existing value.

        - `201` if `key` did not exist yet
        - `200` if an existing value was overwritten

        The database file is updated in the background, so the change is
        persisted shortly after the response is sent.
        """
    ),
    response_description="The existing value was overwritten. Returns the stored value.",
    responses={
        201: {
            "description": "The key was created. Returns the stored value.",
            "model": str,
        },
        503: {"description": "The database file could not be opened and loaded."},
    },
)
def put(
    key: Annotated[
        str, Query(min_length=1, description="The key to store the value under.")
    ],
    value: Annotated[str, Query(description="The value to store.")],
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
    response: Response,
) -> JsonValue:
    parsed_value = parse_value(value)
    stored_value, is_new_key = cache.insert(key, parsed_value)

    response.status_code = status.HTTP_201_CREATED if is_new_key else status.HTTP_200_OK

    background_tasks.add_task(cache.flush)
    return stored_value


@app.get(
    "/db",
    response_model=None,
    summary="Get the value of a key",
    description=cleandoc(
        """
        Returns the value stored under `key`.
        """
    ),
    response_description="The value stored under the key.",
    responses={
        404: {"description": "The requested key does not exist."},
        503: {"description": "The database file could not be opened and loaded."},
    },
)
def get(
    key: Annotated[str, Query(description="The key to look up.")],
    cache: Annotated[Cache, Depends(get_cache)],
) -> JsonValue:
    return cache.select(key)


@app.head(
    "/db",
    response_model=None,
    summary="Check whether a key exists",
    description=cleandoc(
        """
        Checks whether `key` exists without returning its value.

        - `200` if the key exists
        - `404` if it does not

        The response has no body.
        """
    ),
    response_description="The key exists.",
    responses={
        404: {"description": "The requested key does not exist."},
        503: {"description": "The database file could not be opened and loaded."},
    },
)
async def head(
    key: Annotated[str, Query(description="The key to check.")],
    cache: Annotated[Cache, Depends(get_cache)],
) -> JsonValue:
    return cache.select(key)


@app.get(
    "/db/all",
    response_model=None,
    summary="Get all key-value pairs",
    description=cleandoc(
        """
        Returns a snapshot of every key-value pair in the database.
        """
    ),
    response_description="All stored key-value pairs.",
    responses={
        503: {"description": "The database file could not be opened and loaded."}
    },
)
def get_all(cache: Annotated[Cache, Depends(get_cache)]) -> dict[str, JsonValue]:
    with cache.lock:
        return require_db(cache).copy()


@app.get(
    "/db/bulk",
    summary="Get multiple key-value pairs",
    description=cleandoc(
        """
        Returns the values stored in the database under multiple requested keys.

        Keys that do not exist are omitted from the response.
        The response contains a key-value pair for each requested key that exists in the database.
        """
    ),
    response_description="The requested key-value pairs requested.",
    responses={
        422: {
            "description": "Some or all the requested values are not found in the database."
        },
        503: {"description": "The database file could not be opened and loaded."},
    },
)
def get_bulk(
    key: Annotated[list[str], Query()], cache: Annotated[Cache, Depends(get_cache)]
) -> dict[str, JsonValue]:
    with cache.lock:
        db = require_db(cache).copy()
        return {k: db[k] for k in key if k in db}


@app.get(
    "/db/count",
    summary="Count the stored keys",
    description=cleandoc(
        """
        Returns the number of key-value pairs in the database.
        """
    ),
    response_description="The number of stored key-value pairs.",
    responses={
        503: {"description": "The database file could not be opened and loaded."}
    },
)
def count(cache: Annotated[Cache, Depends(get_cache)]):
    with cache.lock:
        return len(require_db(cache).copy())


@app.delete(
    "/db",
    response_model=None,
    summary="Delete a key",
    description=cleandoc(
        """
        Removes `key` from the database and returns its previous value.

        The database file is updated in the background, so the change is
        persisted shortly after the response is sent.
        """
    ),
    response_description="The value the key had before it was deleted.",
    responses={
        404: {"description": "The requested key does not exist."},
        503: {"description": "The database file could not be opened and loaded."},
    },
)
def delete(
    key: Annotated[str, Query(description="The key to remove.")],
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
) -> JsonValue:
    value = cache.delete(key)
    background_tasks.add_task(cache.flush)
    return value


@app.get(
    "/health",
    summary="Check service readiness",
    description=cleandoc(
        """
        Reports whether the database has been loaded and the service can
        handle requests.
        """
    ),
    response_description="The service is ready.",
    responses={503: {"description": "The database has not been loaded."}},
)
def health(cache: Annotated[Cache, Depends(get_cache)]):
    if cache.db is None:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return {"status": "ok"}
