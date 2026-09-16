"""Tests for the TTL (Time-to-Live) feature."""

import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from seriousdb import cache, main


class TTLTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        self.original_db_file = main.DB_FILE
        main.DB_FILE = str(Path(self.tmpdir.name) / ".sdb")
        self.addCleanup(setattr, main, "DB_FILE", self.original_db_file)

        self.client = TestClient(main.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_put_with_ttl_returns_value(self):
        response = self.client.put(
            "/db", params={"key": "session", "value": "abc", "ttl": 60}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "abc")

    def test_get_within_ttl_returns_value(self):
        self.client.put("/db", params={"key": "k", "value": "v", "ttl": 60})
        response = self.client.get("/db", params={"key": "k"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "v")

    def test_get_after_ttl_returns_404(self):
        self.client.put("/db", params={"key": "k", "value": "v", "ttl": 0.1})
        time.sleep(0.2)
        response = self.client.get("/db", params={"key": "k"})
        self.assertEqual(response.status_code, 404)

    def test_put_without_ttl_has_no_expiry(self):
        self.client.put("/db", params={"key": "permanent", "value": "forever"})
        time.sleep(0.1)
        response = self.client.get("/db", params={"key": "permanent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "forever")

    def test_put_with_ttl_removes_ttl_on_overwrite_without_ttl(self):
        self.client.put("/db", params={"key": "k", "value": "v1", "ttl": 0.1})
        time.sleep(0.05)
        self.client.put("/db", params={"key": "k", "value": "v2"})
        time.sleep(0.15)
        response = self.client.get("/db", params={"key": "k"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "v2")

    def test_ttl_persists_to_disk(self):
        self.client.put("/db", params={"key": "k", "value": "v", "ttl": 60})
        on_disk = json.loads(Path(main.DB_FILE).read_text())
        self.assertIn("_v", on_disk)
        self.assertIn("ttl", on_disk)
        self.assertIn("k", on_disk["ttl"])

    def test_no_ttl_uses_legacy_format(self):
        self.client.put("/db", params={"key": "k", "value": "v"})
        on_disk = json.loads(Path(main.DB_FILE).read_text())
        self.assertNotIn("_v", on_disk)
        self.assertEqual(on_disk["k"], "v")

    def test_delete_removes_key(self):
        self.client.put("/db", params={"key": "k", "value": "v"})
        response = self.client.delete("/db", params={"key": "k"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"deleted": "k"})
        response = self.client.get("/db", params={"key": "k"})
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_key_is_idempotent(self):
        response = self.client.delete("/db", params={"key": "nope"})
        self.assertEqual(response.status_code, 200)

    def test_ttl_rejects_negative_value(self):
        response = self.client.put(
            "/db", params={"key": "k", "value": "v", "ttl": -1}
        )
        self.assertEqual(response.status_code, 422)


class CacheUnitTests(unittest.TestCase):
    def test_is_expired_false_when_no_ttl(self):
        c = cache.Cache()
        c.db = {"k": "v"}
        c.ttl = {}
        self.assertFalse(cache.is_expired("k", c))

    def test_is_expired_true_when_past(self):
        c = cache.Cache()
        c.db = {"k": "v"}
        c.ttl = {"k": time.time() - 1}
        self.assertTrue(cache.is_expired("k", c))

    def test_is_expired_false_when_future(self):
        c = cache.Cache()
        c.db = {"k": "v"}
        c.ttl = {"k": time.time() + 999}
        self.assertFalse(cache.is_expired("k", c))

    def test_cleanup_expired_removes_keys(self):
        c = cache.Cache()
        c.db = {"a": "1", "b": "2"}
        c.ttl = {"a": time.time() - 1, "b": time.time() + 999}
        expired = cache.cleanup_expired(c)
        self.assertEqual(expired, ["a"])
        self.assertNotIn("a", c.db)
        self.assertIn("b", c.db)

    def test_load_migrates_legacy_format(self):
        with TemporaryDirectory() as tmpdir:
            db_file = str(Path(tmpdir) / ".sdb")
            with open(db_file, "w") as f:
                json.dump({"default": "default"}, f)
            c = cache.Cache()
            cache.load(db_file, c)
            self.assertEqual(c.db, {"default": "default"})
            self.assertEqual(c.ttl, {})

    def test_load_reads_v2_format(self):
        with TemporaryDirectory() as tmpdir:
            db_file = str(Path(tmpdir) / ".sdb")
            with open(db_file, "w") as f:
                json.dump({"_v": 2, "data": {"k": "v"}, "ttl": {"k": 99999}}, f)
            c = cache.Cache()
            cache.load(db_file, c)
            self.assertEqual(c.db, {"k": "v"})
            self.assertEqual(c.ttl, {"k": 99999})

    def test_flush_uses_legacy_when_no_ttl(self):
        with TemporaryDirectory() as tmpdir:
            db_file = str(Path(tmpdir) / ".sdb")
            c = cache.Cache()
            c.filename = db_file
            c.db = {"k": "v"}
            c.ttl = {}
            cache.flush(c)
            on_disk = json.loads(Path(db_file).read_text())
            self.assertNotIn("_v", on_disk)
            self.assertEqual(on_disk["k"], "v")

    def test_flush_uses_v2_when_ttl_present(self):
        with TemporaryDirectory() as tmpdir:
            db_file = str(Path(tmpdir) / ".sdb")
            c = cache.Cache()
            c.filename = db_file
            c.db = {"k": "v"}
            c.ttl = {"k": 12345}
            cache.flush(c)
            on_disk = json.loads(Path(db_file).read_text())
            self.assertEqual(on_disk["_v"], 2)
            self.assertEqual(on_disk["data"], {"k": "v"})
            self.assertEqual(on_disk["ttl"], {"k": 12345})


if __name__ == "__main__":
    unittest.main()
