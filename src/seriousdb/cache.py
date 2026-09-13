import json
import logging
import os
import time
import typing
from threading import Lock


logger = logging.getLogger(__name__)

DEFAULT_DB: dict[str, str] = {"default": "default"}


class Cache:
    def __init__(self):
        self.filename: str | None = None
        self.db: dict[str, str] | None = None
        self.lock: Lock = Lock()


def _write_default(filename: str) -> dict[str, typing.Any]:
    with open(filename, "wb") as f:
    	# Result of call expression is of type "int" and is not used; assign to variable "_" if this is intentional
        _ = f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)


def load(filename: str, cache: Cache) -> None:
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
                    filename, e, backup,
                )
                cache.db = _write_default(filename)
        cache.filename = filename


def flush(cache: Cache) -> None:
    with cache.lock:
        if cache.db is None or cache.filename is None:
            return

        with open(cache.filename, "wb+") as f:
            _ = f.write(json.dumps(cache.db).encode())
