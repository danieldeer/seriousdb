# API reference

seriousdb is used as a Python library: import the package and call its functions directly.

```python
import seriousdb

seriousdb.set("name", "Alice")
seriousdb.get("name")
```

Keys and values are strings. The first call loads `.sdb` from the working directory; set
`SERIOUSDB_DB_FILE` before importing to [configure its path](configuration.md). Loading and flushing
are automatic; neither is exported as a package function (use `seriousdb.api.load(path)` and
`seriousdb.api.is_loaded()` directly if you need to control them explicitly).

`set` and `delete` write the full database before returning, so a successful call is persisted. See
[persistence](persistence.md) for concurrency and durability limits.

## Functions

| Function          | Description                                                                                               |
|:------------------|:----------------------------------------------------------------------------------------------------------|
| `get(key)`        | Return the value stored under `key`. <br/>Raises `ResourceNotFoundError` if the key does not exist.       |
| `set(key, value)` | Store `value` under `key`, overwriting any existing value.<br/>Returns the stored value.                  |
| `delete(key)`     | Remove `key` and return its previous value.<br/>Raises `ResourceNotFoundError` if the key does not exist. |
| `exists(key)`     | Return whether `key` exists.                                                                              |
| `get_all()`       | Return a snapshot of every key-value pair.                                                                |
| `get_bulk(keys)`  | Return the values for multiple keys; missing keys are omitted.                                            |
| `count()`         | Return the number of stored key-value pairs.                                                              |

## Errors

Missing keys raise `seriousdb.exceptions.ResourceNotFoundError`, as noted above. File access
failures can raise `OSError`; a failed write leaves the in-memory change in place.

| Exception                 | Raised when                                       |
|:--------------------------|:--------------------------------------------------|
| `ResourceNotFoundError`   | The requested key does not exist.                 |
| `ServiceUnavailableError` | The database file could not be opened and loaded. |

Both inherit from `seriousdb.exceptions.ApplicationError`, so callers can catch that base class to
handle any seriousdb-specific failure.
