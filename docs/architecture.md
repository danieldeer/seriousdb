# Architecture

The application is currently intentionally small:

- `main.py` creates the FastAPI application and defines the HTTP routes.
- The database is represented as a Python dictionary in memory while a request is handled.
- The dictionary is loaded from and written to the local `.sdb` file.

The service starts with a default entry when `.sdb` does not exist. There is no separate database process or client library.

## Request flow

1. FastAPI receives a request.
2. A `PUT` reads the value from its JSON request body.
3. The route accesses the in-memory dictionary.
4. A `PUT` updates and rewrites the file; a `GET` reads the requested value.
5. The route returns the value or a `404` error.
