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

Retrieves a page of keys stored in the database, sorted alphabetically.

Parameters:

- `limit` *(optional)* - Maximum number of keys to return. Defaults to `100`. Must be between `1` and `500`.
- `cursor` *(optional)* - Resume point from a previous response's `next_cursor`. Only keys sorting after this value are returned.

For example:

```text
limit: 2
```

returns:

```json
{"keys": ["age", "default"], "next_cursor": "default"}
```

If `next_cursor` is non-null, more keys are available — pass it as `cursor` on the next request to continue:

```text
limit: 2
cursor: default
```

returns:

```json
{"keys": ["name"], "next_cursor": null}
```

A `next_cursor` of `null` means there are no more keys to return.

If `limit` is outside the `1`–`500` range, the API returns a `400` response.


### HEAD `/db`

Checks if the requested key exists in the database.

For example:

```text
key: name
```

If the requested key exists, the API returns a `200` response.

If the requested key does not exist, the API returns a `404` response.
