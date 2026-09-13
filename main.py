import json
import os
from fastapi import FastAPI
from fastapi import HTTPException
from threading import Lock


class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()

    def insert(self, key: str, value: str):
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            self.db[key] = value
        return value


    def select(self, key: str):
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            val = self.db.get(key, None)
        if val is None:
            raise HTTPException(status_code=404, detail=f"No value set for key {key}")
        return val


    def load(self, filename: str):
        with self.lock:
            db_file = filename
            if not os.path.isfile(db_file):
                with open(db_file, "wb") as f:
                    json_dumps = json.dumps({"default": "default"}).encode()
                    f.write(json_dumps)
                self.db = {"default": "default"}
            else:
                with open(filename, "rb") as f:
                    binary_text = f.read()
                    json_text = binary_text.decode()
                    self.db = json.loads(json_text)
            self.filename = filename


    def flush(self):
        with self.lock:
            if self.db is None:
                return
            with open(self.filename, "wb+") as f:
                json_dumps = json.dumps(self.db).encode()
                f.write(json_dumps)


    def delete(self, key: str):
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            if key not in self.db:
                raise HTTPException(status_code=404, detail=f"No value set for key {key}")
            deleted_value = self.db.pop(key)
        return deleted_value


db_file = ".sdb"
cache = Cache()
cache.load(db_file)

app = FastAPI()


@app.delete("/db")
async def delete(key: str):
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
    val = cache.select(key)
    return val
