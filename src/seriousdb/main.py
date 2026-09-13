from fastapi import FastAPI, Depends, Request, status
from starlette.responses import JSONResponse
from dotenv import load_dotenv
from .cache import Cache, load, flush
from .db import insert, select
from .config import DB_FILE
from .auth import is_validated, require_auth

app = FastAPI()
cache = Cache()


@app.on_event("startup")
def startup():
    load(DB_FILE, cache)
    if not load_dotenv():
        if require_auth:
            raise RuntimeError(".env must exist and contain 'AUTH_TOKEN'")


def get_cache() -> Cache:
    return cache


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not is_validated(request):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"status": "Unauthorized"}
        )
    response = await call_next(request)
    return response


@app.put("/db")
async def put(key: str, value: str, cache: Cache = Depends(get_cache)):
    insert(key, value, cache)
    flush(cache)
    return value


@app.get("/db")
async def get(key: str, cache: Cache = Depends(get_cache)):
    return select(key, cache)
