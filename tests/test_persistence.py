import json

from fastapi.testclient import TestClient

from seriousdb import main
from seriousdb.cache import Cache


def test_non_ttl_value_stored_as_plain_string(client: TestClient, tmp_path):
    client.put("/db", params={"key": "plain", "value": "str"})
    data = json.loads((tmp_path / "test.sdb").read_text())
    assert data["plain"] == "str"


def test_ttl_value_stored_with_expiry_metadata(client: TestClient, tmp_path, clock):
    clock.now = 100.0
    client.put("/db", params={"key": "temp", "value": "hi", "ttl": 10})
    data = json.loads((tmp_path / "test.sdb").read_text())
    assert data["temp"] == {"value": "hi", "expires_at": 110.0}


def test_data_survives_restart(tmp_path, monkeypatch):
    db_file = tmp_path / "test.sdb"

    first_cache = Cache()
    monkeypatch.setattr(main, "DB_FILE", db_file)
    monkeypatch.setattr(main, "cache", first_cache)
    with TestClient(main.app) as first_client:
        first_client.put("/db", params={"key": "keep", "value": "me", "ttl": 100})

    second_cache = Cache()
    monkeypatch.setattr(main, "cache", second_cache)
    with TestClient(main.app) as second_client:
        response = second_client.get("/db", params={"key": "keep"})
        assert response.status_code == 200
        assert response.json() == "me"
