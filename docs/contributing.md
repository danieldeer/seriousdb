# Contributing

Keep changes focused and update the relevant documentation when behavior changes.

Before opening a change, format, lint, and type check the Python code:

```bash
uvx ruff format .
uvx ruff check .
uvx ty check
```

When adding or changing an endpoint, update [the API reference](api.md) and verify the behavior through the FastAPI documentation at `/docs` or an HTTP client.
