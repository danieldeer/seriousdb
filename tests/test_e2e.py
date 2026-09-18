"""End-to-end sanity checks for the documented HTTP API.

Every test mirrors a statement from ``docs/api.md`` or ``docs/persistence.md``
and drives the app through FastAPI's ``TestClient``.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seriousdb import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient backed by a throwaway database file.

    Entered as a context manager so that the lifespan handler loads the database.
    """
    monkeypatch.setattr(main, "DB_FILE", str(tmp_path / ".sdb"))

    with TestClient(main.app) as test_client:
        yield test_client


def test_fresh_database_is_empty(client):
    # docs/persistence.md: a new database file is seeded with {}
    response = client.get("/db/all")
    assert response.status_code == 200
    assert response.json() == {}


def test_put_stores_value_and_get_retrieves_it(client):
    put_response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert put_response.status_code == 201
    assert put_response.json() == "Alice"

    get_response = client.get("/db", params={"key": "name"})
    assert get_response.status_code == 200
    assert get_response.json() == "Alice"


def test_put_stores_value_and_head_checks_for_it(client):
    put_response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert put_response.status_code == 201
    assert put_response.json() == "Alice"

    head_response = client.head("/db", params={"key": "name"})
    assert head_response.status_code == 200


def test_put_overwrites_existing_key(client):
    create_response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert create_response.status_code == 201

    update_response = client.put("/db", params={"key": "name", "value": "Bob"})
    assert update_response.status_code == 200

    response = client.get("/db", params={"key": "name"})
    assert response.json() == "Bob"


def test_get_missing_key_returns_404(client):
    # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
    response = client.get("/db", params={"key": "does-not-exist"})
    assert response.status_code == 404


def test_head_missing_key_returns_404(client):
    # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
    response = client.head("/db", params={"key": "does-not-exist"})
    assert response.status_code == 404


def test_put_persists_to_db_file_on_disk(client):
    # docs/persistence.md: each PUT writes the complete dictionary back to disk.
    client.put("/db", params={"key": "name", "value": "Alice"})

    on_disk = json.loads(Path(main.DB_FILE).read_text())
    assert on_disk["name"] == "Alice"


def test_delete_existing_key_removes_it(client):
    put_response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert put_response.status_code == 201

    delete_response = client.delete("/db", params={"key": "name"})
    assert delete_response.status_code == 200

    get_response = client.get("/db", params={"key": "name"})
    assert get_response.status_code == 404


def test_delete_missing_key_returns_404(client):
    response = client.delete("/db", params={"key": "does-not-exist"})
    assert response.status_code == 404


def test_count_returns_number_of_key_value_pairs(client):
    client.put("/db", params={"key": "name", "value": "Alice"})
    client.put("/db", params={"key": "language", "value": "Python"})

    response = client.get("/db/count")

    assert response.status_code == 200
    assert response.json() == 2


def test_bulk_returns_requested_keys(client):
    client.put("/db", params={"key": "name", "value": "Daniel"})
    client.put("/db", params={"key": "language", "value": "Python"})

    response = client.get("/db/bulk", params=[("key", "name"), ("key", "language")])

    assert response.status_code == 200
    assert response.json() == {"name": "Daniel", "language": "Python"}
