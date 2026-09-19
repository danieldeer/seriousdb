# Architecture

The project is currently intentionally small:

- `api.py` exposes the public, module-level functions (`get`, `set`, `delete`, ...) that other Python code imports and calls directly.
- `cache.py` implements `Cache`, an in-memory dictionary guarded by a lock, which the API functions operate on.
- The dictionary is loaded from and written to the local `.sdb` file.

The database starts with zero entries when `.sdb` does not exist. seriousdb runs in the same process as its caller; there is no separate database process.

## Call flow

1. A caller imports `seriousdb` and calls a function, e.g. `seriousdb.set(key, value)`.
2. On first use, the module loads the dictionary from `.sdb` automatically (or from wherever `seriousdb.api.load(path)` was pointed).
3. `set` and `delete` update the in-memory dictionary and immediately flush it back to `.sdb`; `get`, `exists`, `get_all`, `get_bulk` and `count` read the in-memory dictionary directly.
4. The function returns the requested value, or raises an exception (see [Errors](api.md#errors)) if it can't be fulfilled.

Separate `Cache` instances (and separate processes) have independent data and
locks; see [persistence](persistence.md#current-constraints) for the
consequences of using the same file from more than one of them.

## Error handling

`exceptions.py` defines `ApplicationError` and its subclasses; `cache.py` and `api.py` raise them directly wherever an operation can't succeed. Callers handle them like any other Python exception.
