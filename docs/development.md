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

To use a custom database file:
```bash
SERIOUSDB_FILE=/tmp/seriousdb.sdb uv run run.py
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

## Formatting

Format Python files with `ruff`:

```bash
uv tool run ruff format .
```

### Nix in Nix develop

```bash
ruff format .
```

## Linting

Lint python files with `ruff`:

```bash
uv tool run ruff check .
```

### Nix in Nix develop

```bash
ruff check .
```

To fix linter errors and warning if possible run following command:

```bash
uv tool run ruff check --fix .
```

### Nix in Nix develop

```bash
ruff check --fix .
```
