import json
import logging
import os
import time
from threading import Lock

from .exceptions import ResourceNotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


class Cache:
    def __init__(self):
        self.filename: str | None = None
        self.db: dict[str, str] | None = None
        self.ttl: dict[str, float] = {}
        self.lock = Lock()

    def insert(self, key: str, value: str, ttl: float | None = None) -> str:
        with self.lock:
            require_db(self)[key] = value
            if ttl is not None:
                self.ttl[key] = time.time() + ttl
            else:
                self.ttl.pop(key, None)
        return value

    def select(self, key: str) -> str:
        with self.lock:
            if self._is_expired(key):
                require_db(self).pop(key, None)
                del self.ttl[key]
                raise ResourceNotFoundError(f"No value set for key {key}")
            val = require_db(self).get(key, None)
        if val is None:
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def delete(self, key: str) -> str:
        with self.lock:
            val = require_db(self).pop(key, None)
            self.ttl.pop(key, None)
        if val is None:
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def _is_expired(self, key: str) -> bool:
        expires_at = self.ttl.get(key)
        return expires_at is not None and time.time() >= expires_at

    def cleanup_expired(self) -> list[str]:
        now = time.time()
        with self.lock:
            expired = [k for k, exp in self.ttl.items() if now >= exp]
            for k in expired:
                if self.db is not None:
                    self.db.pop(k, None)
                del self.ttl[k]
        return expired

    def load(self, filename: str) -> None:
        with self.lock:
            self.ttl = {}
            if not os.path.isfile(filename):
                self.db = _write_default(filename)
            else:
                try:
                    with open(filename, "rb") as f:
                        raw = json.loads(f.read().decode())
                    if isinstance(raw, dict) and "_v" in raw:
                        self.db = raw["data"]
                        self.ttl = raw.get("ttl", {})
                    else:
                        self.db = raw
                        if not isinstance(self.db, dict):
                            raise TypeError(
                                f"expected dict, got {type(self.db).__name__}"
                            )
                except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as e:
                    backup = f"{filename}.corrupt-{int(time.time())}"
                    os.replace(filename, backup)
                    logger.warning(
                        "Corrupt database file %s (%s); moved to %s and starting fresh",
                        filename,
                        e,
                        backup,
                    )
                    self.db = _write_default(filename)
            self.filename = filename

    def flush(self) -> None:
        with self.lock:
            if self.db is None or self.filename is None:
                return
            payload = (
                {"_v": 2, "data": self.db, "ttl": self.ttl} if self.ttl else self.db
            )
            with open(self.filename, "wb+") as f:
                f.write(json.dumps(payload).encode())


def _write_default(filename: str) -> dict[str, str]:
    with open(filename, "wb") as f:
        f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)


def require_db(cache: Cache) -> dict[str, str]:
    """Return the loaded database or fail with an expected application error."""
    if cache.db is None:
        raise ServiceUnavailableError(
            f"Database file {cache.filename} could not be opened and loaded"
        )
    return cache.db
