# Architecture

The application is currently intentionally small:

- `main.py` creates the FastAPI application and defines the HTTP routes.
- The database is represented as a Python dictionary in memory while a request is handled.
- The dictionary is loaded from and written to the local `.sdb` file.

The service starts with a default entry when `.sdb` does not exist. There is no separate database process or client library.

## Request flow

1. FastAPI receives a request.
2. The route loads the dictionary from `.sdb`.
3. A `PUT` inserts into the in-memory dictionary and schedules a
   background flush to disk; A `GET` reads the requested value; A `HEAD`
   only returns the header; A`DELETE` removes the key and schedules a
   background flush to disk.
4. The route returns the value or a `404` error.

## Error handling

`exceptions.py` defines `ApplicationError` and its subclasses; `cache.py` and the routes raise them instead of `HTTPException`. `error_handlers.py` translates them into the responses documented in [the API reference](api.md) and answers anything unexpected with a generic `500`.
