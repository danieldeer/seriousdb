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
        self.ttl = {}
        self.lock = Lock()


def is_expired(key: str, cache: Cache) -> bool:
    expires_at = cache.ttl.get(key)
    return expires_at is not None and time.time() >= expires_at


def cleanup_expired(cache: Cache) -> list[str]:
    now = time.time()
    expired = [k for k, exp in cache.ttl.items() if now >= exp]
    for k in expired:
        cache.db.pop(k, None)
        del cache.ttl[k]
    return expired


def _write_default(filename: str) -> dict:
    with open(filename, "wb") as f:
        f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)


def load(filename: str, cache: Cache):
    with cache.lock:
        cache.ttl = {}
        if not os.path.isfile(filename):
            cache.db = _write_default(filename)
        else:
            try:
                with open(filename, "rb") as f:
                    raw = json.loads(f.read().decode())
                if isinstance(raw, dict) and "_v" in raw:
                    cache.db = raw["data"]
                    cache.ttl = raw.get("ttl", {})
                else:
                    cache.db = raw
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
        payload = (
            {"_v": 2, "data": cache.db, "ttl": cache.ttl}
            if cache.ttl
            else cache.db
        )
        with open(cache.filename, "wb+") as f:
            f.write(json.dumps(payload).encode())
