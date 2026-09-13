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

## Pre-commit hooks

This project uses [`pre-commit`](https://pre-commit.com/) to run linting, formatting, and other
checks automatically before each commit. After syncing the dev dependencies, install the git
hooks once:

```bash
uv run pre-commit install
```

To run all hooks against the entire repository (e.g. before opening a pull request):

```bash
uv run pre-commit run --all-files
```

The configured hooks (see `.pre-commit-config.yaml`) include `uv lock` sync checks, trailing
whitespace/end-of-file fixers, YAML/TOML validation, `ruff` linting and formatting, and `ty`
type checking.

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

### Nix in Nix develop

```bash
ruff check .
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

### Nix in Nix develop

```bash
ruff check --fix .
```
