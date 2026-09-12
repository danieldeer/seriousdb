
import pickle

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.sdb"
    with open(db_file, "wb") as f:
        pickle.dump({"default": "default"}, f)
    monkeypatch.setattr(main, "db_file", str(db_file))
    return TestClient(main.app)


def test_put_and_get_roundtrip(client):
    put_response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert put_response.status_code == 200
    assert put_response.json() == "Alice"

    get_response = client.get("/db", params={"key": "name"})
    assert get_response.status_code == 200
    assert get_response.json() == "Alice"


def test_get_default_key(client):
    response = client.get("/db", params={"key": "default"})
    assert response.status_code == 200
    assert response.json() == "default"


def test_get_missing_key_returns_404(client):
    response = client.get("/db", params={"key": "does-not-exist"})
    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]


def test_put_overwrites_existing_key(client):
    assert client.put("/db", params={"key": "name", "value": "Alice"}).status_code == 200
    assert client.put("/db", params={"key": "name", "value": "Bob"}).status_code == 200

    response = client.get("/db", params={"key": "name"})
    assert response.status_code == 200
    assert response.json() == "Bob"


def test_put_does_not_delete_other_keys(client):
    client.put("/db", params={"key": "a", "value": "1"})
    client.put("/db", params={"key": "b", "value": "2"})

    assert client.get("/db", params={"key": "a"}).json() == "1"
    assert client.get("/db", params={"key": "b"}).json() == "2"
    assert client.get("/db", params={"key": "default"}).json() == "default"


def test_get_without_key_returns_validation_error(client):
    response = client.get("/db")
    assert response.status_code == 422


def test_put_without_value_returns_validation_error(client):
    response = client.put("/db", params={"key": "name"})
    assert response.status_code == 422
