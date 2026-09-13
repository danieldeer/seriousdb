import json
import os
from threading import Lock
from fastapi import HTTPException


class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()


    def load(self, filename: str):
        with self.lock:
            if not os.path.isfile(filename):
                with open(filename, "wb") as f:
                    f.write(json.dumps({"default": "default"}).encode())
                self.db = {"default": "default"}
            else:
                with open(filename, "rb") as f:
                    self.db = json.loads(f.read().decode())
            self.filename = filename


    def flush(self):
        with self.lock:
            if self.db is None:
                return
            with open(self.filename, "wb+") as f:
                f.write(json.dumps(self.db).encode())

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
