# API reference

The server exposes a small HTTP API through FastAPI.

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

### PUT `/db`

Stores or updates a key-value pair.

Parameters:

- `key` - The key to store.
- `value` - The value associated with the key. The value is parsed as JSON, allowing strings, numbers, booleans, `null`, arrays, and objects.

For example:

```text
key: name
value: Alice
```

This stores:

```python
{"name": "Alice"}
```

Numbers and other JSON values can also be stored:

```text
key: age
value: 42
```

stores:

```python
{"age": 42}
```

To store a number as a string, use JSON string syntax:

```text
key: code
value: "42"
```

This stores:

```python
{"code": "42"}
```

The same applies to other JSON values:

```text
value: 3.14
value: true
value: false
value: null
value: [1, 2, 3]
value: {"name": "Alice"}
```

These are stored as their corresponding JSON/Python types.

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
