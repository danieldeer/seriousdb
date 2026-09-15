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
        put_response = self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), "Alice")

        get_response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), "Alice")

    def test_put_stores_value_and_head_checks_for_it(self):
        put_response = self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.assertEqual(put_response.status_code, 200)
        self.assertEqual(put_response.json(), "Alice")

        head_response = self.client.head("/db", params={"key": "name"})
        self.assertEqual(head_response.status_code, 200)

    def test_put_overwrites_existing_key(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "name", "value": "Bob"})

        response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(response.json(), "Bob")

    def test_get_missing_key_returns_404(self):
        # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
        response = self.client.get("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_head_missing_key_returns_404(self):
        # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
        response = self.client.get("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_put_persists_to_db_file_on_disk(self):
        # docs/persistence.md: each PUT writes the complete dictionary back to disk.
        self.client.put("/db", params={"key": "name", "value": "Alice"})

        on_disk = json.loads(Path(main.DB_FILE).read_text())
        self.assertEqual(on_disk["name"], "Alice")

    def test_get_keys_on_fresh_database_returns_seeded_default_key(self):
        # docs/persistence.md: a new database file is seeded with {"default": "default"}
        response = self.client.get("/db/keys")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["default"])

    def test_get_keys_returns_list_type(self):
        response = self.client.get("/db/keys")
        self.assertIsInstance(response.json(), list)

    def test_get_keys_reflects_newly_put_key(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})

        response = self.client.get("/db/keys")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json())

    def test_get_keys_returns_multiple_keys(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "age", "value": "30"})

        response = self.client.get("/db/keys")
        self.assertCountEqual(response.json(), ["default", "name", "age"])

    def test_get_keys_does_not_duplicate_on_overwrite(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "name", "value": "Bob"})

        response = self.client.get("/db/keys")
        self.assertEqual(response.json().count("name"), 1)

    def test_get_keys_excludes_deleted_key(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.delete("/db", params={"key": "name"})

        response = self.client.get("/db/keys")
        self.assertNotIn("name", response.json())


if __name__ == "__main__":
    unittest.main()
