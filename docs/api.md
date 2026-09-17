# API reference

The server exposes a small HTTP API through FastAPI.

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

An example inserting value `"Alice"` into key `"name"` using curl:
```shell
curl -X 'PUT' \
  'http://localhost:8000/db?key=name&value=Alice' \
  -H 'accept: */*'
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

An example getting the value associated with key `"name"` using curl:
```shell
curl -X 'GET' \
  'http://localhost:8000/db?key=name' \
  -H 'accept: */*'
```

returns:

```text
Alice
```

If the requested key does not exist, the API returns a `404` response.

### GET `/health`

Reports whether the database cache has finished loading.

Getting the health status using curl:
```shell
curl -X 'GET' \
  'http://localhost:8000/health' \
  -H 'accept: */*'
```

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

Checking if key `"name"` exists in the database with curl:
```shell
curl -X 'HEAD' \
  'http://localhost:8000/db?key=name' \
  -H 'accept: */*'
```

If the requested key exists, the API returns a `200` response.

If the requested key does not exist, the API returns a `404` response.

### GET `/db/bulk`

Retrieves the values for multiple keys in a single request.

For example:

```text
GET /db/bulk?key=name&key=language
```

Getting multiple keys with curl:
```shell
curl -X 'GET' \
  'http://localhost:8000/db/bulk?key=name&key=language' \
  -H 'accept: */*'
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

Getting all key-value pairs in the database with curl:
```shell
curl -X 'GET' \
  'http://localhost:8000/db/all' \
  -H 'accept: */*'
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

Then running
```shell
curl -X 'GET' \
  'http://localhost:8000/db/count' \
  -H 'accept: */*'
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
Using curl:
```shell
curl -X 'DELETE' \
  'http://localhost:8000/db?key=name' \
  -H 'accept: */*'
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
