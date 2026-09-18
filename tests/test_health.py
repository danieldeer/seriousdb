"""Tests for the readiness endpoint."""

import pytest
from fastapi.testclient import TestClient

from seriousdb import main
from seriousdb.cache import Cache


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient backed by a throwaway database file and an empty cache.

    The module-level cache is emptied so that startup has to load it, and
    ``monkeypatch`` restores it afterwards.
    """
    monkeypatch.setattr(main.cache, "filename", None)
    monkeypatch.setattr(main.cache, "db", None)
    monkeypatch.setattr(main, "DB_FILE", str(tmp_path / "test.sdb"))

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def unavailable_client(monkeypatch):
    """A TestClient whose cache never gets loaded, without running startup."""
    unloaded = Cache()
    monkeypatch.setitem(main.app.dependency_overrides, main.get_cache, lambda: unloaded)

    return TestClient(main.app)


def test_health_reports_ready_after_startup_loads_cache(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_reports_unavailable_cache(unavailable_client):
    response = unavailable_client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service unavailable",
        "error": "service_unavailable",
    }
