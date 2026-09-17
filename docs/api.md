# API reference

The server exposes a small HTTP API through FastAPI.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

## Example usage

The following examples assume the server is running on `http://127.0.0.1:8000`.

Store a value under a key:

```bash
curl -X PUT "http://127.0.0.1:8000/db?key=name&value=Alice"
```

Retrieve a stored value:

```bash
curl "http://127.0.0.1:8000/db?key=name"
```

Check whether a key exists:

```bash
curl -I "http://127.0.0.1:8000/db?key=name"
```

Delete a key:

```bash
curl -X DELETE "http://127.0.0.1:8000/db?key=name"
```

Empty-string keys are valid in SeriousDB, so this is also allowed:

```bash
curl -X PUT "http://127.0.0.1:8000/db?key=&value=Alice"
curl "http://127.0.0.1:8000/db?key="
```

A missing `key` parameter is still considered invalid and returns `422`.

### PUT `/db`

Stores or updates a key-value pair.

- If the key does not exist yet, the API respond with `201 Created`.
- If the key already exists, the API respond with `200 OK` and overwrites the stored value.

Parameters:

- `key` - The key to store. The empty string is valid and treated as a real key value.
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

The empty string is also a valid key, so `GET /db?key=` will retrieve the value stored under that empty key.

If the requested non-empty key does not exist, the API returns a `404` response.

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

The empty string is a valid key, so `HEAD /db?key=` checks whether the empty-key record exists.

If the requested non-empty key does not exist, the API returns a `404` response.

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

- `key` - The key to delete. The empty string is valid and deletes the empty-key record if it exists.

For example:

```text
key: name
```

If the key exists, the API returns its previous value.

If the requested non-empty key does not exist, the API returns a `404` response.

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
