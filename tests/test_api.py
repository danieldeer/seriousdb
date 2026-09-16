import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from seriousdb import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / ".sdb"

    with open(db_file, "w") as f:
        json.dump({}, f)

    monkeypatch.setattr(main, "DB_FILE", str(db_file))

    with TestClient(main.app) as test_client:
        yield test_client


def test_put_stores_value(client):
    response = client.put(
        "/db",
        params={"key": "test_key", "value": "test_value"},
    )

    assert response.status_code == 201
    assert response.json() == "test_value"


def test_get_returns_stored_value(client):
    client.put(
        "/db",
        params={"key": "test_key", "value": "test_value"},
    )

    response = client.get(
        "/db",
        params={"key": "test_key"},
    )

    assert response.status_code == 200
    assert response.json() == "test_value"


def test_get_missing_key_returns_404(client):
    response = client.get(
        "/db",
        params={"key": "does_not_exist"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No value set for key does_not_exist",
        "error": "resource_not_found",
    }


def test_get_all_returns_all_values(client):
    client.put(
        "/db",
        params={"key": "name", "value": "Alice"},
    )

    client.put(
        "/db",
        params={"key": "language", "value": "Python"},
    )

    response = client.get("/db/all")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "language": "Python",
    }


def test_put_empty_key_returns_422(client):
    response = client.put(
        "/db",
        params={"key": "", "value": "test_value"},
    )

    assert response.status_code == 422


def test_put_missing_key_returns_422(client):
    response = client.put(
        "/db",
        params={"value": "test_value"},
    )

    assert response.status_code == 422


def test_put_missing_value_returns_422(client):
    response = client.put(
        "/db",
        params={"key": "test_key"},
    )

    assert response.status_code == 422


def test_get_missing_key_parameter_returns_422(client):
    response = client.get("/db")

    assert response.status_code == 422


def test_delete_missing_key_parameter_returns_422(client):
    response = client.delete("/db")

    assert response.status_code == 422


def test_put_updates_existing_key(client):
    response = client.put(
        "/db",
        params={"key": "name", "value": "Alice"},
    )
    assert response.status_code == 201
    assert response.json() == "Alice"

    response = client.put(
        "/db",
        params={"key": "name", "value": "Bob"},
    )

    assert response.status_code == 200
    assert response.json() == "Bob"

    response = client.get(
        "/db",
        params={"key": "name"},
    )

    assert response.status_code == 200
    assert response.json() == "Bob"


def test_concurrent_put_requests(client):
    def put_value(number):
        response = client.put(
            "/db",
            params={
                "key": f"key_{number}",
                "value": f"value_{number}",
            },
        )
        return response

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(put_value, range(10)))

    assert all(response.status_code == 201 for response in responses)

    response = client.get("/db/all")

    assert response.status_code == 200

    db = response.json()

    for number in range(10):
        assert db[f"key_{number}"] == f"value_{number}"


def test_concurrent_put_and_delete_requests(client):
    for number in range(10):
        client.put(
            "/db",
            params={
                "key": f"delete_{number}",
                "value": f"value_{number}",
            },
        )

    def delete_value(number):
        return client.delete(
            "/db",
            params={"key": f"delete_{number}"},
        )

    def put_value(number):
        return client.put(
            "/db",
            params={
                "key": f"put_{number}",
                "value": f"value_{number}",
            },
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        delete_futures = [executor.submit(delete_value, number) for number in range(10)]
        put_futures = [executor.submit(put_value, number) for number in range(10)]

        delete_responses = [future.result() for future in delete_futures]
        put_responses = [future.result() for future in put_futures]

    assert all(response.status_code == 200 for response in delete_responses)
    assert all(response.status_code == 201 for response in put_responses)

    response = client.get("/db/all")

    assert response.status_code == 200

    db = response.json()

    for number in range(10):
        assert f"delete_{number}" not in db
        assert db[f"put_{number}"] == f"value_{number}"


def test_count_returns_number_of_key_value_pairs(client):
    client.put(
        "/db",
        params={"key": "name", "value": "Alice"},
    )

    client.put(
        "/db",
        params={"key": "language", "value": "Python"},
    )

    response = client.get("/db/count")

    assert response.status_code == 200
    assert response.json() == 2


def test_count_return_zero_on_empty_db(client):
    response = client.get("/db/count")

    assert response.status_code == 200
    assert response.json() == 0


def test_count_decreases_after_deleting_key(client):
    client.put(
        "/db",
        params={"key": "name", "value": "Alice"},
    )

    response = client.get("/db/count")

    assert response.status_code == 200
    assert response.json() == 1

    response = client.delete(
        "/db",
        params={"key": "name"},
    )

    assert response.status_code == 200

    response = client.get("/db/count")

    assert response.status_code == 200
    assert response.json() == 0


def test_bulk_returns_requested_keys(client):
    client.put(
        "/db",
        params={"key": "name", "value": "Daniel"},
    )

    client.put(
        "/db",
        params={"key": "language", "value": "Python"},
    )

    response = client.get(
        "/db/bulk",
        params=[("key", "name"), ("key": "language")],
    )

    assert response.status_code == 200
    assert response.json() == {"name": "Alice", "language": "Python"}


def test_bulk_omits_missing_keys(client):
    client.put(
        "/db",
        params={"key": "name", "value": "Daniel"},
    )

    response = client.get(
        "db/bulk",
        params=[("key", "name"), ("key", "does_not_exist")],
    )

    assert response.status_code == 200
    assert response.json() == {"name": "Daniel"}


def test_bulk_returns_empty_object_when_no_keys_match(client):
    response = client.get(
        "/db/bulk",
        params=[("key", "does_not_exist")],
    )

    assert response.status_code == 200
    assert response.json() == {}


def test_bulk_missing_key_parameter_returns_422(client):
    response = client.get("/db/bulk")

    assert response.status_code == 422
