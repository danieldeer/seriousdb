import json
from pathlib import Path
from threading import Lock


class Cache:
    """In-memory key-value store backed by a JSON file on disk."""

    def __init__(self) -> None:
        """Initialize an empty, unbound cache."""
        self.filename: str | None = None
        self.db = None
        self.lock = Lock()


def load(filename: str, cache: Cache) -> None:
    """Load `filename` into `cache`, creating it with default contents if missing."""
    with cache.lock:
        path = Path(filename)
        if not path.is_file():
            with path.open("wb") as f:
                f.write(json.dumps({"default": "default"}).encode())
            cache.db = {"default": "default"}
        else:
            with path.open("rb") as f:
                cache.db = json.loads(f.read().decode())
        cache.filename = filename


def flush(cache: Cache) -> None:
    """Persist `cache`'s in-memory database back to its backing file."""
    with cache.lock:
        if cache.db is None or cache.filename is None:
            return
        with Path(cache.filename).open("wb+") as f:
            f.write(json.dumps(cache.db).encode())
