import json
import logging
import os
import time
from threading import Lock

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()


def _write_default(filename: str) -> dict:
    with open(filename, "wb") as f:
        f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)


def load(filename: str, cache: Cache):
    with cache.lock:
        if not os.path.isfile(filename):
            cache.db = _write_default(filename)
        else:
            try:
                with open(filename, "rb") as f:
                    cache.db = json.loads(f.read().decode())
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                backup = f"{filename}.corrupt-{int(time.time())}"
                os.replace(filename, backup)
                logger.warning(
                    "Corrupt database file %s (%s); moved to %s and starting fresh",
                    filename,
                    e,
                    backup,
                )
                cache.db = _write_default(filename)
        cache.filename = filename


def flush(cache: Cache):
    with cache.lock:
        if cache.db is None:
            return
        with open(cache.filename, "wb+") as f:
            f.write(json.dumps(cache.db).encode())
