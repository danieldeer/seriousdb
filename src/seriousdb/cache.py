import json
import logging
import time
from pathlib import Path
from threading import Lock

from fastapi import HTTPException

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


class Cache:
    """In-memory key-value store backed by a JSON file on disk."""

    def __init__(self) -> None:
        """Initialize an empty, unbound cache."""
        self.filename: str | None = None
        self.db = None
        self.lock = Lock()

    def insert(self, key: str, value: str) -> str:
        """Insert `value` under `key` and return it."""
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            self.db[key] = value
        return value

    def select(self, key: str) -> str:
        """Return the value stored under `key`."""
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

    def delete(self, key: str) -> str:
        """Remove and return the value stored under `key`."""
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

    def load(self, filename: str) -> None:
        """Load `filename` into the cache, recovering from a missing or corrupt file."""
        with self.lock:
            path = Path(filename)
            if not path.is_file():
                self.db = _write_default(path)
            else:
                try:
                    self.db = json.loads(path.read_bytes().decode())
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    backup = path.with_name(f"{path.name}.corrupt-{int(time.time())}")
                    path.replace(backup)
                    logger.warning(
                        "Corrupt database file %s (%s); moved to %s and starting fresh",
                        filename,
                        e,
                        backup,
                    )
                    self.db = _write_default(path)
            self.filename = filename

    def flush(self) -> None:
        """Persist the in-memory database back to its backing file."""
        with self.lock:
            if self.db is None or self.filename is None:
                return
            Path(self.filename).write_bytes(json.dumps(self.db).encode())


def _write_default(path: Path) -> dict:
    path.write_bytes(json.dumps(DEFAULT_DB).encode())
    return dict(DEFAULT_DB)
