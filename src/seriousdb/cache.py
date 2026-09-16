import json
import logging
import os
import time
from threading import Lock

from .exceptions import ResourceNotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_DB = {}


class Cache:
    def __init__(self):
        self.filename: str | None = None
        self.db: dict[str, str] | None = None
        self.lock = Lock()

    def insert(self, key: str, value: str) -> tuple[str, bool]:
        with self.lock:
            db = require_db(self)
            is_new_key = key not in db
            db[key] = value
        return value, is_new_key

    def select(self, key: str) -> str:
        with self.lock:
            val = require_db(self).get(key, None)
        if val is None:
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def delete(self, key: str) -> str:
        with self.lock:
            val = require_db(self).pop(key, None)
        if val is None:
            raise ResourceNotFoundError(f"No value set for key {key}")
        return val

    def load(self, filename: str) -> None:
        with self.lock:
            if not os.path.isfile(filename):
                self.db = _write_default(filename)
            else:
                try:
                    with open(filename, "rb") as f:
                        self.db = json.loads(f.read().decode())
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
            with open(self.filename, "wb+") as f:
                f.write(json.dumps(self.db).encode())


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
