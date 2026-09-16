# Testing

The project uses `pytest` for automated testing and FastAPI's `TestClient` for API testing.

## Running the Tests

Run the full test suite with:

```bash
uv run pytest
```

The test suite covers:

- API endpoint behavior
- Validation behavior
- CRUD operations
- Concurrent database access

Each test uses an isolated temporary database so the test suite does not modify the local `.sdb` database.
