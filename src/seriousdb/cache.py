import json
import logging
import os
import time
import types
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from threading import Lock
from typing import Union, get_args, get_origin

from .exceptions import ResourceNotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_DB = {"default": "default"}


@dataclass
class Cache:
    filename: str | None = None
    db: dict[str, str] | None = None
    lock: Lock = field(default_factory=Lock, init=False)

    def __post_init__(self):
        for f in dataclass_fields(self):
            field_name = f.name
            defined_type = f.type
            value = getattr(self, field_name)

            origin = get_origin(defined_type)
            is_union = origin is Union or (
                hasattr(types, "UnionType") and origin is types.UnionType
            )

            allowed_types = get_args(defined_type) if is_union else (defined_type,)

            # Check if None is allowed for this field
            none_allowed = type(None) in allowed_types
            if value is None:
                if none_allowed:
                    continue
                else:
                    raise TypeError(
                        f"Field '{field_name}' cannot be None, expected '{defined_type}'"
                    )

            #  Extract base classes for runtime checking (e.g., dict[str, str] -> dict)
            base_types = tuple((get_origin(t) or t) for t in allowed_types)

            #  Outer structural check
            if not isinstance(value, base_types):
                raise TypeError(
                    f"Field '{field_name}' got an invalid type: '{type(value).__name__}' expected '{defined_type}'"
                )

            if (
                isinstance(value, dict)
                and any(t == dict[str, str] for t in allowed_types)
                and not all(
                    isinstance(k, str) and isinstance(v, str) for k, v in value.items()
                )
            ):
                raise TypeError(
                    f"Field '{field_name}' must be a dict[str, str], but contains non-string elements."
                )

    def insert(self, key: str, value: str) -> str:
        with self.lock:
            require_db(self)[key] = value
        return value

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
