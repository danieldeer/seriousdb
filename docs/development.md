# Development guide

## Requirements

- Python 3.11 or newer
- `uv`

## Setup

```bash
uv sync
```

## Run locally

```bash
uv run fastapi dev main.py
```

The server is available at `http://127.0.0.1:8000` and its interactive API documentation is at `/docs`.

## Formatting

Format Python files with Black:

```bash
uv tool run black main.py
```
