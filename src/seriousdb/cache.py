import json
import logging
import os
import tempfile
import time
from threading import Lock

from fastapi import HTTPException

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


class Cache:
    def __init__(self):
        self.filename: str | None = None
        self.db: dict[str, str] | None = None
        self.lock = Lock()

    def insert(self, key: str, value: str) -> str:
        with self.lock:
            if self.db is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database file {self.filename} could not be opened and loaded",
                )
            self.db[key] = value
        return value

    def select(self, key: str) -> str:
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

    def flush(self) -> None:
        with self.lock:
            if self.db is None or self.filename is None:
                return
            _atomic_write(self.filename, json.dumps(self.db).encode())

def _atomic_write(filename: str, data: bytes) -> None:
    directory = os.path.dirname(os.path.abspath(filename))

    fd, temp_filename = tempfile.mkstemp(
            dir=directory,
            prefix=f".{os.path.basename(filename)}.",
            suffix=".tmp"
            )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            f.fsync(f.fileno())

        os.replace(temp_filename, filename)
    except Exception:
        try:
            os.unlink(temp_filename)
        except FileNoFoundError:
            pass
        raise

def _write_default(filename: str) -> dict[str, str]:
    data = json.dumps(DEFAULT_DB).encode()
    _atomic_write(filename, data)
    return dict(DEFAULT_DB)
