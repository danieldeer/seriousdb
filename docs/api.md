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

All functions operate on a single shared cache and are thread-safe.
The database file (default: `.sdb`) is loaded automatically on the first call.
Use `seriousdb.load(path)` to load a different file explicitly.

`set` and `delete` flush the database file before they return, so a successful call is persisted.

| Function | Description |
| :--- | :--- |
| `get(key)` | Return the value stored under `key`. Raises `ResourceNotFoundError` if the key does not exist. |
| | |
| `set(key, value)` | Store `value` under `key`, overwriting any existing value. Returns the stored value. |
| | |
| `delete(key)` | Remove `key` and return its previous value. Raises `ResourceNotFoundError` if the key does not exist. |
| | |
| `exists(key)` | Return whether `key` exists. |
| | |
| `get_all()` | Return a snapshot of every key-value pair. |
| | |
| `get_bulk(keys)` | Return the values for multiple keys; missing keys are omitted. |
| | |
| `count()` | Return the number of stored key-value pairs. |
| | |
| `load(path)` | Load (or create) a database file, replacing the current data. |
| | |
| `flush()` | Write the current data to the database file. |
| | |
| `is_loaded()` | Return whether a database has been loaded. |

The Python API raises the same application exceptions as the HTTP layer,
e.g. `seriousdb.exceptions.ResourceNotFoundError`.


## HTTP API

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### PUT `/db`

Stores or updates a key-value pair.

- If the key does not exist yet, the API respond with `201 Created`.
- If the key already exists, the API respond with `200 OK` and overwrites the stored value.

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
{ "status": "ok" }
```

If the cache is not ready, it returns `503`:

```json
{ "detail": "Service unavailable" }
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

Keys that do not exist in the database are omitted from response. If no `key` parameter is provided, the API returns a `422` response.

### GET `/db/all`

Retrieves all key-value pairs currently stored in the database.

For example:

```text
GET /db/all
```

returns:

```json
{
  "default": "default",
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
  "default": "default",
  "name": "Alice",
  "language": "Python"
}
```

returns:

```text
3
```

> **Note:** The count includes the `default` key if it is present in the database.

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

## Error responses

All errors share the same JSON structure:

```json
{
  "detail": "No value set for key name",
  "error": "resource_not_found"
}
```

- `detail` - a human readable message. For request validation errors this is the list of problems reported by FastAPI.
- `error` - a stable, machine readable code.

| Status | `error`                    | Meaning                                                      |
| ------ | -------------------------- | ------------------------------------------------------------ |
| `404`  | `resource_not_found`       | The requested key does not exist.                            |
| `422`  | `request_validation_error` | A required query parameter is missing or has the wrong type. |
| `503`  | `service_unavailable`      | The database file could not be opened and loaded.            |
| `500`  | `internal_server_error`    | An unexpected error. Details are never returned.             |
