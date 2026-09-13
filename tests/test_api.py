from fastapi.testclient import TestClient


def test_put_and_get_roundtrip(client: TestClient):
    response = client.put("/db", params={"key": "name", "value": "Alice"})
    assert response.status_code == 200
    assert response.json() == "Alice"

    response = client.get("/db", params={"key": "name"})
    assert response.status_code == 200
    assert response.json() == "Alice"


def test_get_missing_key_returns_404(client: TestClient):
    response = client.get("/db", params={"key": "missing"})
    assert response.status_code == 404


def test_default_entry_created_on_first_startup(client: TestClient):
    response = client.get("/db", params={"key": "default"})
    assert response.status_code == 200
    assert response.json() == "default"


def test_put_updates_existing_key(client: TestClient):
    client.put("/db", params={"key": "name", "value": "Alice"})
    response = client.put("/db", params={"key": "name", "value": "Bob"})
    assert response.status_code == 200

    response = client.get("/db", params={"key": "name"})
    assert response.json() == "Bob"


def test_put_with_ttl_returns_value_before_expiry(client: TestClient):
    response = client.put("/db", params={"key": "session", "value": "abc", "ttl": 60})
    assert response.status_code == 200

    response = client.get("/db", params={"key": "session"})
    assert response.status_code == 200
    assert response.json() == "abc"


def test_put_with_ttl_returns_404_after_expiry(client: TestClient, clock):
    client.put("/db", params={"key": "session", "value": "abc", "ttl": 10})
    clock.now += 10.0

    response = client.get("/db", params={"key": "session"})
    assert response.status_code == 404

    response = client.get("/db", params={"key": "session"})
    assert response.status_code == 404


def test_put_with_non_positive_ttl_rejected(client: TestClient):
    for ttl in (0, -5):
        response = client.put("/db", params={"key": "bad", "value": "x", "ttl": ttl})
        assert response.status_code == 422
