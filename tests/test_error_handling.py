"""Tests for the centralized application errors and FastAPI exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from seriousdb import main
from seriousdb.cache import Cache, require_db
from seriousdb.error_handlers import (
    INTERNAL_ERROR_DETAIL,
    register_exception_handlers,
)
from seriousdb.exceptions import (
    ApplicationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)


@pytest.fixture
def handler_client():
    """A minimal app of its own, used to exercise the handlers in isolation."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    def not_found():
        raise ResourceNotFoundError("nothing here")

    @app.get("/unavailable")
    def unavailable():
        raise ServiceUnavailableError("database is gone")

    @app.get("/boom")
    def boom():
        raise RuntimeError("connection string admin:hunter2 failed")

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient for the real application, backed by a throwaway database file.

    Entered as a context manager so that the lifespan handler loads the database.
    Dependency overrides are cleared afterwards so that a test replacing the cache
    cannot leak into the next one.
    """
    monkeypatch.setattr(main, "DB_FILE", str(tmp_path / ".sdb"))
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.clear()


class TestApplicationExceptions:
    @pytest.mark.parametrize(
        "subclass", [ResourceNotFoundError, ServiceUnavailableError]
    )
    def test_subclasses_share_the_application_error_base(self, subclass):
        assert issubclass(subclass, ApplicationError)

    def test_detail_defaults_to_the_class_default(self):
        assert str(ResourceNotFoundError()) == ResourceNotFoundError.default_detail

    def test_detail_can_be_overridden(self):
        assert str(ResourceNotFoundError("no such key")) == "no such key"

    def test_require_db_returns_the_loaded_database(self):
        cache = Cache()
        cache.db = {"default": "default"}
        assert require_db(cache) is cache.db

    def test_require_db_raises_service_unavailable_without_a_database(self):
        cache = Cache()
        cache.filename = ".sdb"
        with pytest.raises(ServiceUnavailableError, match=r"\.sdb"):
            require_db(cache)


class TestHandlers:
    """Handlers are exercised through a minimal app of their own."""

    def test_resource_not_found_maps_to_404(self, handler_client):
        response = handler_client.get("/not-found")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "nothing here",
            "error": "resource_not_found",
        }

    def test_service_unavailable_maps_to_503(self, handler_client):
        response = handler_client.get("/unavailable")
        assert response.status_code == 503
        assert response.json() == {
            "detail": "database is gone",
            "error": "service_unavailable",
        }

    def test_unexpected_error_does_not_leak_details(self, handler_client):
        response = handler_client.get("/boom")

        assert response.status_code == 500
        assert response.json() == {
            "detail": INTERNAL_ERROR_DETAIL,
            "error": "internal_server_error",
        }
        assert "hunter2" not in response.text

    def test_unknown_route_uses_the_standard_error_structure(self, handler_client):
        response = handler_client.get("/no-such-route")
        assert response.status_code == 404
        assert sorted(response.json()) == ["detail", "error"]


class TestApiErrorResponses:
    """The real application returns the standard structure for its own errors."""

    @pytest.mark.parametrize("method", ["GET", "DELETE"])
    def test_missing_key_returns_a_structured_404(self, client, method):
        response = client.request(method, "/db", params={"key": "does-not-exist"})
        assert response.status_code == 404
        assert response.json() == {
            "detail": "No value set for key does-not-exist",
            "error": "resource_not_found",
        }

    @pytest.mark.parametrize(
        ("method", "url", "params"),
        [
            pytest.param("GET", "/db", {"key": "name"}, id="get"),
            pytest.param("PUT", "/db", {"key": "name", "value": "Alice"}, id="put"),
            pytest.param("DELETE", "/db", {"key": "name"}, id="delete"),
            pytest.param("GET", "/db/all", {}, id="get-all"),
        ],
    )
    def test_unloaded_database_returns_503(self, client, method, url, params):
        unloaded = Cache()
        unloaded.filename = "missing.sdb"
        main.app.dependency_overrides[main.get_cache] = lambda: unloaded

        response = client.request(method, url, params=params)

        assert response.status_code == 503
        assert response.json()["error"] == "service_unavailable"
        assert "missing.sdb" in response.json()["detail"]

    def test_missing_query_parameter_returns_a_structured_422(self, client):
        response = client.get("/db")
        assert response.status_code == 422
        assert response.json()["error"] == "request_validation_error"

    def test_rejected_query_parameter_returns_a_structured_422(self, client):
        response = client.put("/db", params={"key": "", "value": "Alice"})
        assert response.status_code == 422
        assert response.json()["error"] == "request_validation_error"
