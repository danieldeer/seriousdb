import json
import logging
import os
import time
from threading import Lock

from fastapi import HTTPException

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


class Cache:
    def __init__(self):
        self.filename = None
        self.db = None
        self.lock = Lock()

    def insert(self, key: str, value: str):
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            self.db[key] = value
        return value

    def select(self, key: str):
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=500,
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
                    status_code=500,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            val = self.db.pop(key, None)
        if val is None:
            raise HTTPException(status_code=404, detail=f"No value set for key {key}")
        return val

    def load(self, filename: str):
        with self.lock:
            if not os.path.isfile(filename):
                self.db = _write_default(filename)
            else:
                try:
                    with open(filename, "rb") as f:
                        self.db = json.loads(f.read().decode())
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
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

    def flush(self):
        with self.lock:
            if self.db is None:
                return
            with open(self.filename, "wb+") as f:
                f.write(json.dumps(self.db).encode())

    def keys(
        self, limit: int, cursor: str | None = None
    ) -> tuple[list[str], str | None]:
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            all_keys = sorted(self.db.keys())

        if cursor:
            all_keys = [k for k in all_keys if k > cursor]

        page = all_keys[:limit]
        next_cursor = page[-1] if len(page) == limit else None

        return page, next_cursor


def _write_default(filename: str) -> dict:
    with open(filename, "wb") as f:
        f.write(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)
