# API reference

The server exposes a small HTTP API through FastAPI.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### PUT `/db`

Stores or updates a key-value pair.

Parameters:

* `key` - The key to store. Must contain at least one character.
* `value` - The value associated with the key.

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
{"status": "ok"}
```

If the cache is not ready, it returns `503`:

```json
{"detail": "Service unavailable"}
```

### HEAD `/db`

Checks if the requested key exists in the database.

For example:

```text
key: name
```

If the requested key exists, the API returns a `200` response.

If the requested key does not exist, the API returns a `404` response.

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

### DELETE `/db`

Deletes a key-value pair.

Parameters:

* `key` - The key to delete.

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

* `detail` - a human readable message. For request validation errors this is the list of problems reported by FastAPI.
* `error` - a stable, machine readable code.

| Status  | `error`                    | Meaning                                                      |
| ------- | ---------------------------| ------------------------------------------------------------ |
| `404`   | `resource_not_found`       | The requested key does not exist.                            |
| `422`   | `request_validation_error` | A required query parameter is missing or has the wrong type. |
| `503`   | `service_unavailable`      | The database file could not be opened and loaded.            |
| `500`   | `internal_server_error`    | An unexpected error. Details are never returned.             |
