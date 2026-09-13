import json
import os
from threading import Lock


class Cache:
    def __init__(self):
        self.filename: str | None = None
        self.db = None
        self.lock = Lock()


def load(filename: str, cache: Cache):
    with cache.lock:
        if not os.path.isfile(filename):
            with open(filename, "wb") as f:
                f.write(json.dumps({"default": "default"}).encode())
            cache.db = {"default": "default"}
        else:
            with open(filename, "rb") as f:
                cache.db = json.loads(f.read().decode())
        cache.filename = filename


def flush(cache: Cache):
    with cache.lock:
        if cache.db is None or cache.filename is None:
            return
        with open(cache.filename, "wb+") as f:
            f.write(json.dumps(cache.db).encode())
