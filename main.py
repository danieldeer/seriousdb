import pickle
import os
from fastapi import FastAPI
from fastapi import HTTPException

class Cache:
    def __init__(self):
        self.filename = None
        self.db = None


def insert(key: str, value: str, cache: Cache):
    if cache.db is None:
        raise HTTPException(status_code=404, detail=f"Database file {cache.filename} could not be opened and loaded")
    cache.db[key] = value
    return value

def select(key: str, cache : Cache):
    if cache.db is None:
        raise HTTPException(status_code=404, detail=f"Database file {cache.filename} could not be opened and loaded")
    val = cache.db.get(key, None)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val

def load(filename: str, cache : Cache):
    db_file = filename
    if not os.path.isfile(db_file):
        with open(db_file, "wb") as f:
            pickle.dump({"default": "default"}, f)
    else:
        with open(filename, "rb") as f:
            cache.db = pickle.load(f)
    cache.filename = filename

def flush(cache : Cache):
    if cache.db is None:
        return
    with open(cache.filename, "wb+") as f:
        pickle.dump(cache.db, f)

db_file = ".sdb"
cache = Cache()
load(db_file, cache)

app = FastAPI()

@app.put("/db")
async def put(key: str, value: str):
    insert(key, value, cache)
    flush(cache)
    return value

@app.get("/db")
async def get(key: str):
    val = select(key, cache)
    return val
