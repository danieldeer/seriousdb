# API reference

The server exposes a small HTTP API through FastAPI.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### PUT `/db`

Stores or updates a key-value pair.

Parameters:

- `key` - The key to store.
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

### GET `/db/keys`

Lists stored keys, paginated.

Parameters:
- `limit` - Maximum number of keys to return. Default to `100`, Capped at `1000`.
- `offset` - Number of keys to skip before collecting results. Default to `0`.

For example, if the database contains:

```python
{"default": "default", "name": "Alice"}
```

`GET /db/keys`(default params) returns:

```text
["default", "name"]
```

`GET /db/keys?limit=1` returns:

```text
["default"]
```

`GET /db/keys?offset=1` returns:

```text
["name"]
```

NOTE: this endpoint currently has no authentication or authrization, consistent with the rest of the API.Key enumeration is therefore only as safe as the deployment it's runnin in.
