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

    def test_fresh_database_is_empty(self):
        # docs/persistence.md: a new database file is seeded with {}
        response = self.client.get("/db/all")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_put_stores_value_and_get_retrieves_it(self):
        put_response = self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.assertEqual(put_response.status_code, 201)
        self.assertEqual(put_response.json(), "Alice")

        get_response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), "Alice")

    def test_put_stores_value_and_head_checks_for_it(self):
        put_response = self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.assertEqual(put_response.status_code, 201)
        self.assertEqual(put_response.json(), "Alice")

        head_response = self.client.head("/db", params={"key": "name"})
        self.assertEqual(head_response.status_code, 200)

    def test_put_overwrites_existing_key(self):
        create_response = self.client.put(
            "/db", params={"key": "name", "value": "Alice"}
        )
        self.assertEqual(create_response.status_code, 201)

        update_response = self.client.put("/db", params={"key": "name", "value": "Bob"})
        self.assertEqual(update_response.status_code, 200)

        response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(response.json(), "Bob")

    def test_get_missing_key_returns_404(self):
        # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
        response = self.client.get("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_head_missing_key_returns_404(self):
        # docs/api.md: "If the requested key does not exist, the API returns a 404 response."
        response = self.client.head("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_put_persists_to_db_file_on_disk(self):
        # docs/persistence.md: each PUT writes the complete dictionary back to disk.
        self.client.put("/db", params={"key": "name", "value": "Alice"})

        on_disk = json.loads(Path(main.DB_FILE).read_text())
        self.assertEqual(on_disk["name"], "Alice")

    def test_delete_existing_key_removes_it(self):
        put_response = self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.assertEqual(put_response.status_code, 201)

        delete_response = self.client.delete("/db", params={"key": "name"})
        self.assertEqual(delete_response.status_code, 200)

        get_response = self.client.get("/db", params={"key": "name"})
        self.assertEqual(get_response.status_code, 404)

    def test_delete_missing_key_returns_404(self):
        response = self.client.delete("/db", params={"key": "does-not-exist"})
        self.assertEqual(response.status_code, 404)

    def test_count_returns_number_of_key_value_pairs(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "language", "value": "Python"})

        response = self.client.get("/db/count")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 2)


if __name__ == "__main__":
    unittest.main()
