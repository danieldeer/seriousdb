# API reference

The server exposes a small HTTP API through FastAPI.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### PUT `/db`

Stores or updates a key-value pair.

Parameters:

- `key` - The key to store.
- `value` - The value associated with the key.
- `ttl` - Optional. Time-to-live in seconds. When provided, the key expires
  and is no longer returned after that many seconds have elapsed.

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

Storing a value that expires after 60 seconds:

```text
key: session
value: abc123
ttl: 60
```

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

If the requested key has expired, it is removed and the API returns a `404`
response (lazy expiration).
