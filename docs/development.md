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

### Enter Nix develop

```bash
nix develop
```

## Starting in Nix develop

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

Format Python files with `ruff`:

```bash
uv run ruff format .
```

To check formatting without changing files:

```bash
uv run ruff format --check .
```

### Nix in Nix develop

```bash
ruff format .
```

## Linting

Lint python files with `ruff`:

```bash
uv run ruff check .
```

Type checking with `ty`:
```bash
uv run ty check .
```

### Nix in Nix develop

```bash
ruff check .
```

To fix linter errors and warning if possible run following command:

```bash
uv run ruff check --fix .
```

### Nix in Nix develop

```bash
ruff check --fix .
```

## Docstrings

Python docstrings follow the [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html).
See [`cache.py`](../src/seriousdb/cache.py) for examples.

Docstrings are required for public functions, classes and modules only; for private ones (prefixed with `_`) they are optional.
This is enforced by `ruff` (see [Linting](#linting)).

### Endpoints

Don't write docstrings for FastAPI endpoints. Document them through the route
decorator instead (`summary=`, `description=`, `response_description=`,
`responses=`), so the text shows up in the OpenAPI docs at `/docs`.
See [`main.py`](../src/seriousdb/main.py) for examples.
