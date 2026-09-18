# Development guide

## Requirements

- Python 3.11 or newer
- `uv`

## Setup

```bash
uv sync
```

To sync development dependencies run following command:

```bash
uv sync --group dev
```

## Run locally

```bash
uv run run.py 
```

## Nix

>The project provides a Nix development environment with the tools required for local development.

### Enter Nix develop

From the project root, run:

```bash
nix develop
```

This starts a shell with the project's development dependencies available.

## Nix (in the Nix Shell) 

```bash
python run.py
```

## Docker

```bash
docker build -t seriousdb .
docker run -p 8000:8000 seriousdb
```

The server is available at `http://127.0.0.1:8000` and its interactive API documentation is at `/docs`.

The readiness endpoint is available at `/health`.

## Formatting

### Format Python files with `ruff`:

#### uv

```bash
uv run ruff format .
```

### Nix (in Nix Shell)

```bash
ruff format .
```

### To check formatting without changing files:

#### uv

```bash
uv run ruff format --check .
```

### Nix (in Nix Shell)

```bash
ruff format --check .
```

## Linting

### Lint python files with `ruff`:

#### uv

```bash
uv run ruff check .
```

#### Nix (in Nix Shell)

```bash
ruff check .
```

### Type checking with `ty`

#### uv

```bash
uv run ty check .
```

#### Nix (in Nix Shell)

```bash
ty check .
```

### To fix linter errors and warning if possible run following command:

#### uv

```bash
uv run ruff check --fix .
```

### Nix (in Nix Shell)

```bash
ruff check --fix .
```

## Docstrings

Python docstrings follow the [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html).

Docstrings are required for public functions, classes and modules only; for private ones (prefixed with `_`) they are optional.
This is enforced by `ruff` (see [Linting](#linting)).

A docstring starts with a one-line summary, followed by the sections that apply, such as `Parameters`, `Returns` and `Raises`:

```python
def select(self, key: str) -> str:
    """Return the value stored under `key`.

    Parameters
    ----------
    key : str
        Key to look up.

    Returns
    -------
    str
        The value stored under `key`.

    Raises
    ------
    ResourceNotFoundError
        If `key` does not exist.
    ServiceUnavailableError
        If no database has been loaded.
    """
```

See [`cache.py`](../src/seriousdb/cache.py) for more examples.

### Endpoints

Don't write docstrings for FastAPI endpoints. Document them through the route
decorator instead (`summary=`, `description=`, `response_description=`,
`responses=`), so the text shows up in the OpenAPI docs at `/docs`.
Describe query parameters with `Query(description=...)`.

`description` supports Markdown. Wrap multi-line descriptions in
`inspect.cleandoc` so the indentation doesn't break the rendering:

```python
@app.delete(
    "/db",
    summary="Delete a key",
    description=cleandoc(
        """
        Removes `key` from the database and returns its previous value.

        The database file is updated in the background, so the change is
        persisted shortly after the response is sent.
        """
    ),
    response_description="The value the key had before it was deleted.",
    responses={
        404: {"description": "The requested key does not exist."},
        503: {"description": "The database file could not be opened and loaded."},
    },
)
def delete(
    key: Annotated[str, Query(description="The key to remove.")],
    background_tasks: BackgroundTasks,
    cache: Annotated[Cache, Depends(get_cache)],
) -> str:
    value = cache.delete(key)
    background_tasks.add_task(cache.flush)
    return value
```

See [`main.py`](../src/seriousdb/main.py) for more examples.
