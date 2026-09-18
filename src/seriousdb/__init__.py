"""SeriousDB, a small persistent key-value database.

seriousdb can be used as a storage layer from other Python projects.
>>> import seriousdb
>>> seriousdb.set("name", "Alice")
'Alice'
>>> seriousdb.get("name")
'Alice'
"""

from seriousdb.api import (
    cache,
    count,
    delete,
    exists,
    flush,
    get,
    get_all,
    get_bulk,
    is_loaded,
    load,
    set,
)

__all__ = [
    "cache",
    "count",
    "delete",
    "exists",
    "flush",
    "get",
    "get_all",
    "get_bulk",
    "is_loaded",
    "load",
    "set",
]
