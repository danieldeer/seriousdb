import importlib
import unittest
from unittest.mock import patch

from seriousdb import config


class ConfigTests(unittest.TestCase):
    def test_db_file_configured_from_environment(self):
        self.addCleanup(importlib.reload, config)

        with patch.dict("os.environ", {"SERIOUSDB_FILE": "/tmp/test-seriousdb.sdb"}):
            reloaded = importlib.reload(config)

        self.assertEqual(reloaded.DB_FILE, "/tmp/test-seriousdb.sdb")


if __name__ == "__main__":
    unittest.main()
