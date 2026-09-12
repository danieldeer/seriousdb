# seriousdb - An HTTP-based Key-Value Store

`seriousdb` is a small HTTP-based key-value store written in Python using [FastAPI](https://fastapi.tiangolo.com/).

Data is stored in a local `.sdb` file.

## Running the Server

Start the server with:

```bash
fastapi dev main.py
```

The server will be available at:

```text
http://127.0.0.1:8000
```

FastAPI also provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## API

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

### DELETE `/db`

Deletes a key-value pair.

Parameters:

- `key` - The key to delete.

For example:

```text
key: name
```

If the key exists, the endpoint deletes it and returns its previous value.

If the requested key does not exist, the API returns a `404` response.

## Persistence

Data is stored locally in a `.sdb` file.
