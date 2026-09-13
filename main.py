import json
import os
import tempfile
from fastapi import FastAPI, HTTPException
from threading import Lock

class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()

def insert(key: str, value: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database not initialized")
        cache.db[key] = value
    return value

def select(key: str, cache: Cache):
    with cache.lock:
        if cache.db is None:
            raise HTTPException(status_code=404, detail=f"Database not initialized")
        val = cache.db.get(key, None)
        if val is None:
            raise HTTPException(status_code=404, detail=f"No value set for key {key}")
        return val

def load(filename: str, cache: Cache):
    with cache.lock:
        if not os.path.isfile(filename):
            with open(filename, "w") as f:
                json.dump({"default": "default"}, f)
            cache.db = {"default": "default"}
        else:
            with open(filename, "r") as f:
                cache.db = json.load(f)
        cache.filename = filename

def flush(cache: Cache):
    with cache.lock:
        if cache.db is None or cache.filename is None:
            return
        
        dir_name = os.path.dirname(os.path.abspath(cache.filename))
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tf:
            json.dump(cache.db, tf)
            temp_name = tf.name
            
        os.replace(temp_name, cache.filename)

db_file = ".sdb"
cache = Cache()
load(db_file, cache)

app = FastAPI()

@app.put("/db")
def put(key: str, value: str):
    insert(key, value, cache)
    flush(cache)
    return value

@app.get("/db")
def get(key: str):
    return select(key, cache)
