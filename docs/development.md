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
uv run run.py 
```

The server is available at `http://127.0.0.1:8000` and its interactive API documentation is at `/docs`.

## Docker

```bash
docker build -t seriousdb .
docker run -p 8000:8000 seriousdb
```

## Formatting

Format Python files with Black:

```bash
uv tool run black main.py
```
