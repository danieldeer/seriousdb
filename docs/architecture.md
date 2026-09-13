# Architecture

The application is currently intentionally small, every souce file is located under the `src/` directory:

- `db.py` loads the database from the local `.sdb` file into memory once at
  startup, and exposes it alongside a `threading.Lock` and a `save_db`
  function for persisting changes.
- `api.py` creates the FastAPI application and defines the HTTP routes.
- `main.py` runs the application with uvicorn.

The service starts with a default entry when `.sdb` does not exist. There is
no separate database process or client library.

## Request flow

1. FastAPI receives a request.
2. The route accesses the in-memory dictionary under a lock (no disk read).
3. A `PUT` updates the in-memory dictionary and writes it to `.sdb`; a `GET`
   reads the requested value from memory only.
4. The route returns the value or a `404` error.