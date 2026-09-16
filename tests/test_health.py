import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from seriousdb import main
from seriousdb.cache import Cache


@contextmanager
def isolated_cache(database_path: Path):
    original_filename = main.cache.filename
    original_db = main.cache.db
    try:
        main.cache.filename = None
        main.cache.db = None
        with (
            patch.object(main, "DB_FILE", database_path),
            TestClient(main.app) as client,
        ):
            yield client
    finally:
        main.cache.filename = original_filename
        main.cache.db = original_db


class HealthEndpointTests(unittest.TestCase):
    def test_health_reports_ready_after_startup_loads_cache(self):
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "test.sdb"
            with isolated_cache(database_path) as client:
                response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_reports_unavailable_cache(self):
        cache = Cache()
        main.app.dependency_overrides[main.get_cache] = lambda: cache

        try:
            response = TestClient(main.app).get("/health")
        finally:
            main.app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "detail": "Service unavailable",
                "error": "service_unavailable",
            },
        )


if __name__ == "__main__":
    unittest.main()
