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

### HEAD `/db`

Checks if the requested key exists in the database.

For example:

```text
key: name
```

If the requested key exists, the API returns a `200` response.

If the requested key does not exist, the API returns a `404` response.



### DELETE `/db`

Deletes a key-value pair

```text
key: name
```
If the key exists, both the key and it's associated value are deleted. The API returns `204` response with no content in the reponse body.

If the requested key does not exist, the API returns a `404`