"""Tests for config values coming from the environment (see .env.example, README)."""

import importlib
import os
import unittest

from seriousdb import config


class ConfigEnvTests(unittest.TestCase):
    ENV_KEYS = ("SERIOUSDB_DB_FILE", "SERIOUSDB_LOG_LEVEL")

    def setUp(self):
        self.saved = {key: os.environ.get(key) for key in self.ENV_KEYS}
        for key in self.ENV_KEYS:
            os.environ.pop(key, None)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _reload(self):
        return importlib.reload(config)

    def test_uses_safe_defaults_when_env_is_unset(self):
        reloaded = self._reload()
        self.assertEqual(reloaded.DB_FILE, ".sdb")
        self.assertEqual(reloaded.LOG_LEVEL, "INFO")

    def test_db_file_is_read_from_environment(self):
        os.environ["SERIOUSDB_DB_FILE"] = "custom.sdb"
        reloaded = self._reload()
        self.assertEqual(reloaded.DB_FILE, "custom.sdb")

    def test_log_level_is_read_from_environment(self):
        os.environ["SERIOUSDB_LOG_LEVEL"] = "DEBUG"
        reloaded = self._reload()
        self.assertEqual(reloaded.LOG_LEVEL, "DEBUG")


if __name__ == "__main__":
    unittest.main()
