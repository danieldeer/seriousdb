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

The server is available at `http://127.0.0.1:8000` and its interactive API documentation is at `/docs`.

## Docker

```bash
docker build -t seriousdb .
docker run -p 8000:8000 seriousdb
```

## Formatting

Format Python files with `ruff`:

```bash
uvx ruff format .
```

## Linting

Lint python files with `ruff`:

```bash
uvx ruff check .
```

To fix linter errors and warning if possible run following command:

```bash
uvx ruff check --fix .
```

## Type checking

Type check the project with `ty`:

```bash
uvx ty check
```
