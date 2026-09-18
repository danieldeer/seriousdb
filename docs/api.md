# API reference

seriousdb can be used as a storage layer directly from Python, or through
the small HTTP API exposed by the FastAPI server.

## Python API

Other Python projects can import seriousdb and call its functions directly.

```python
import seriousdb

seriousdb.set("name", "Alice")
seriousdb.get("name")
```

Keys and values are strings. The first call loads `.sdb` from the working
directory; set `SERIOUSDB_DB_FILE` before importing to [configure its path](configuration.md).
Loading and flushing are automatic; neither is exported as a package function.

`set` and `delete` write the full database before returning. Calls share one cache
per process, separate from the HTTP cache. See [persistence](persistence.md) for
concurrency and durability limits.

| Function          | Description                                                                                           |
|:------------------|:------------------------------------------------------------------------------------------------------|
| `get(key)`        | Return the value stored under `key`. Raises `ResourceNotFoundError` if the key does not exist.        |
| `set(key, value)` | Store `value` under `key`, overwriting any existing value. Returns the stored value.                  |
| `delete(key)`     | Remove `key` and return its previous value. Raises `ResourceNotFoundError` if the key does not exist. |
| `exists(key)`     | Return whether `key` exists.                                                                          |
| `get_all()`       | Return a snapshot of every key-value pair.                                                            |
| `get_bulk(keys)`  | Return the values for multiple keys; missing keys are omitted.                                        |
| `count()`         | Return the number of stored key-value pairs.                                                          |

Missing keys raise `seriousdb.exceptions.ResourceNotFoundError` as noted above;
file access failures can raise `OSError`. Failed writes leave the in-memory change
in place.

## HTTP API

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

HTTP writes flush in the background after responding; success does not confirm a
file write. See the [write sequence](architecture.md#loading-and-writes).

### PUT `/db`

Stores or updates a key-value pair.

- If the key does not exist yet, the API responds with `201 Created`.
- If the key already exists, the API responds with `200 OK` and overwrites the stored value.

Parameters:

- `key` - The key to store. Must contain at least one character.
- `value` - The value associated with the key.

For example:

```text
key: name
value: Alice
```

This stores:

```python
{"name": "Alice"}
```

alongside any existing key-value pairs.

If the key is empty, the API returns a `422` response.

### GET `/db`

Retrieves the value associated with a key.

For example:

```text
key: name
```

returns:

```text
Alice
```

If the requested key does not exist, the API returns a `404` response.

### GET `/health`

Reports whether the database cache has finished loading.

When the service is ready, the endpoint returns `200`:

```json
{
  "status": "ok"
}
```

If the cache is not ready, it returns `503`:

```json
{
  "detail": "Service unavailable",
  "error": "service_unavailable"
}
```

### HEAD `/db`

Checks if the requested key exists in the database.

For example:

```text
key: name
```

If the requested key exists, the API returns a `200` response.

If the requested key does not exist, the API returns a `404` response.

### GET `/db/bulk`

Retrieves the values for multiple keys in a single request.

For example:

```text
GET /db/bulk?key=name&key=language
```

returns:

```json
{
  "name": "Daniel",
  "language": "Python"
}
```

Keys that do not exist in the database are omitted from the response. If no `key` parameter is provided, the API returns a `422` response.

### GET `/db/all`

Retrieves all key-value pairs currently stored in the database.

For example:

```text
GET /db/all
```

returns:

```json
{
  "name": "Alice",
  "language": "Python"
}
```

### GET `/db/count`

Returns the number of key-value pairs currently stored in the database.

For example:

```text
GET /db/count
```

If the database contains:

```json
{
  "name": "Alice",
  "language": "Python"
}
```

returns:

```text
2
```

### DELETE `/db`

Deletes a key-value pair.

Parameters:

- `key` - The key to delete.

For example:

```text
key: name
```

If the key exists, the API returns its previous value.

If the requested key does not exist, the API returns a `404` response.

## HTTP error responses

HTTP error responses with a body use this JSON structure. `HEAD` responses have
no body, including on errors:

```json
{
  "detail": "No value set for key name",
  "error": "resource_not_found"
}
```

- `detail` - a human-readable message. For request validation errors this is the list of problems reported by FastAPI.
- `error` - a stable, machine-readable code.

| Status | `error`                    | Meaning                                                      |
|--------|----------------------------|--------------------------------------------------------------|
| `404`  | `resource_not_found`       | The requested key does not exist.                            |
| `422`  | `request_validation_error` | A required query parameter is missing or has the wrong type. |
| `503`  | `service_unavailable`      | The database file could not be opened and loaded.            |
| `500`  | `internal_server_error`    | An unexpected error. Details are never returned.             |
