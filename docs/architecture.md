# Architecture

The application is currently intentionally small:

- `src/seriousdb/main.py` creates the FastAPI application and defines the HTTP routes.
- The database is represented as a Python dictionary in memory while a request is handled.
- The dictionary is loaded from and written to the local `.sdb` file.

At startup, the service loads `.sdb` into the in-memory dictionary. It creates the file with a default entry when the file does not exist. There is no separate database process or client library.

## Request flow

1. FastAPI receives a request.
2. A `PUT` reads the value from its JSON request body.
3. The route accesses the in-memory dictionary loaded from `.sdb` at startup.
4. A `PUT` updates the dictionary and schedules it to be written to disk; a `GET` reads the requested value; a `HEAD` only returns the header; a `DELETE` deletes the requested key.
5. The route returns the value or a standard error response.

## Error handling

`exceptions.py` defines `ApplicationError` and its subclasses; `cache.py` and the routes raise them instead of `HTTPException`. `error_handlers.py` translates them into the responses documented in [the API reference](api.md) and answers anything unexpected with a generic `500`.
