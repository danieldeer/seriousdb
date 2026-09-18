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

The tests are plain pytest functions. Setup and cleanup happen in fixtures, using the
built-in `tmp_path` and `monkeypatch` fixtures, so each test uses an isolated temporary
database and the test suite does not modify the local `.sdb` database.
