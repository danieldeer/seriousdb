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
        self.assertEqual(response.json(), {"keys": ["default"], "next_cursor": None})

    def test_get_keys_returns_expected_shape(self):
        response = self.client.get("/db/keys")
        body = response.json()
        self.assertIn("keys", body)
        self.assertIn("next_cursor", body)
        self.assertIsInstance(body["keys"], list)

    def test_get_keys_reflects_newly_put_key(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})

        response = self.client.get("/db/keys")
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json()["keys"])

    def test_get_keys_returns_multiple_keys_sorted(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "age", "value": "30"})

        response = self.client.get("/db/keys")
        self.assertEqual(response.json()["keys"], sorted(["default", "name", "age"]))

    def test_get_keys_does_not_duplicate_on_overwrite(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.put("/db", params={"key": "name", "value": "Bob"})

        response = self.client.get("/db/keys")
        self.assertEqual(response.json()["keys"].count("name"), 1)

    def test_get_keys_excludes_deleted_key(self):
        self.client.put("/db", params={"key": "name", "value": "Alice"})
        self.client.delete("/db", params={"key": "name"})

        response = self.client.get("/db/keys")
        self.assertNotIn("name", response.json()["keys"])

    def test_get_keys_respects_limit(self):
        for i in range(5):
            self.client.put("/db", params={"key": f"key{i}", "value": "v"})

        response = self.client.get("/db/keys", params={"limit": 2})
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(body["keys"]), 2)
        self.assertIsNotNone(body["next_cursor"])

    def test_get_keys_last_page_has_no_next_cursor(self):
        for i in range(3):
            self.client.put("/db", params={"key": f"key{i}", "value": "v"})

        response = self.client.get("/db/keys", params={"limit": 100})
        body = response.json()
        self.assertIsNone(body["next_cursor"])

    def test_get_keys_cursor_resumes_after_given_key(self):
        for i in range(5):
            self.client.put("/db", params={"key": f"key{i}", "value": "v"})

        first_page = self.client.get("/db/keys", params={"limit": 2}).json()
        second_page = self.client.get(
            "/db/keys", params={"limit": 2, "cursor": first_page["next_cursor"]}
        ).json()

        self.assertTrue(all(k > first_page["next_cursor"] for k in second_page["keys"]))
        self.assertNotEqual(first_page["keys"], second_page["keys"])

    def test_get_keys_paginates_through_all_keys_without_duplicates_or_gaps(self):
        expected_keys = set()
        for i in range(7):
            key = f"key{i}"
            self.client.put("/db", params={"key": key, "value": "v"})
            expected_keys.add(key)
        expected_keys.add("default")  # seeded key

        collected = []
        cursor = None
        while True:
            params = {"limit": 3}
            if cursor:
                params["cursor"] = cursor
            body = self.client.get("/db/keys", params=params).json()
            collected.extend(body["keys"])
            cursor = body["next_cursor"]
            if cursor is None:
                break

        self.assertEqual(set(collected), expected_keys)
        self.assertEqual(len(collected), len(set(collected)))  # no duplicates

    def test_get_keys_rejects_limit_over_max(self):
        response = self.client.get("/db/keys", params={"limit": 501})
        self.assertEqual(response.status_code, 400)

    def test_get_keys_rejects_zero_limit(self):
        response = self.client.get("/db/keys", params={"limit": 0})
        self.assertEqual(response.status_code, 400)

    def test_get_keys_rejects_negative_limit(self):
        response = self.client.get("/db/keys", params={"limit": -5})
        self.assertEqual(response.status_code, 400)

    def test_get_keys_accepts_max_limit_exactly(self):
        response = self.client.get("/db/keys", params={"limit": 500})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
