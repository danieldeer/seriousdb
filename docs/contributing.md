# Contributing

Keep changes focused and update the relevant documentation when behavior changes.

Before opening a change, format the Python code:

'Classic'-Use:
```bash
uv tool run black .
```

When adding or changing an endpoint, update [the API reference](api.md) and verify the behavior through the FastAPI documentation at `/docs` or an HTTP client.
