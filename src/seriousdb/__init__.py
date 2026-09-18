"""SeriousDB, a small persistent key-value database.

seriousdb can be used as a storage layer from other Python projects.
>>> import seriousdb as sdb
>>> sdb.set("name", "Alice")
'Alice'
>>> sdb.get("name")
'Alice'
"""

from seriousdb.api import (
    count,
    delete,
    exists,
    get,
    get_all,
    get_bulk,
    load,
    set,
)

__all__ = [
    "count",
    "delete",
    "exists",
    "get",
    "get_all",
    "get_bulk",
    "load",
    "set",
]
