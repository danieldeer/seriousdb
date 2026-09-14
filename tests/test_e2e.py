"""End-to-end sanity checks for the documented HTTP API (see docs/api.md, docs/persistence.md).

Uses only stdlib unittest and FastAPI's TestClient, both already available via the
project's existing `fastapi[standard]` dependency (no extra packages required).
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from seriousdb import main


class DocumentedApiTests(unittest.TestCase):
    def setUp(self):
        tmpdir = TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)

        original_db_file = main.DB_FILE
        main.DB_FILE = str(Path(tmpdir.name) / ".sdb")
        self.addCleanup(setattr, main, "DB_FILE", original_db_file)

        self.client = TestClient(main.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_fresh_database_seeds_documented_default_key(self):
        # docs/persistence.md: a new database file is seeded with {"default": "default"}
        response = self.client.get("/db", params={"key": "default"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "default")

    def test_put_stores_value_and_get_retrieves_it(self):
        put_response = self.client.put(
            "/db", params={"key": "name"}, json={"value": "Alice"}
        )
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), "Alice")

        get_response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), "Alice")

    def test_put_overwrites_existing_key(self):
        self.client.put("/db", params={"key": "name"}, json={"value": "Alice"})
        self.client.put("/db", params={"key": "name"}, json={"value": "Bob"})

        response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(response.json(), "Bob")

    def test_get_missing_key_returns_404(self):
        # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
        response = self.client.get("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_put_persists_to_db_file_on_disk(self):
        # docs/persistence.md: each PUT writes the complete dictionary back to disk.
        self.client.put("/db", params={"key": "name"}, json={"value": "Alice"})

        on_disk = json.loads(Path(main.DB_FILE).read_text())
        self.assertEqual(on_disk["name"], "Alice")


if __name__ == "__main__":
    unittest.main()
