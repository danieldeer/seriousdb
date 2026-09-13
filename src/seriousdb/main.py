from fastapi import FastAPI, Depends
from .cache import Cache
from .config import DB_FILE

app = FastAPI()
cache = Cache()

def get_cache() -> Cache:
    return cache

@app.on_event("startup")
def startup():
    cache.load(DB_FILE)

@app.delete("/db")
async def delete(key: str, cache: Cache = Depends(get_cache)):
    deleted_value = cache.delete(key)
    cache.flush()
    return {
        "key": key,
        "deleted_value": deleted_value,
    }

@app.put("/db")
async def put(key: str, value: str):
    cache.insert(key, value)
    cache.flush()
    return value


@app.get("/db")
async def get(key: str):
    return cache.select(key)
