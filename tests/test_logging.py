"""Tests for centralized logging configuration and usage."""

import logging

import pytest

from seriousdb.cache import Cache, require_db
from seriousdb.exceptions import ServiceUnavailableError
from seriousdb.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _isolate_root_logger():
    """Snapshot and restore the root logger so tests don't bleed into each other."""
    root = logging.getLogger()
    old_level = root.level
    old_handlers = root.handlers[:]
    yield
    root.handlers = old_handlers
    root.setLevel(old_level)


class TestConfigureLogging:
    """Tests for the central logging setup function."""

    def test_default_level_is_info(self, monkeypatch):
        monkeypatch.setattr("seriousdb.logging_config.LOG_LEVEL", "INFO")
        configure_logging()
        assert logging.getLogger().level == logging.INFO

    def test_custom_level_debug(self, monkeypatch):
        monkeypatch.setattr("seriousdb.logging_config.LOG_LEVEL", "DEBUG")
        configure_logging()
        assert logging.getLogger().level == logging.DEBUG

    def test_custom_level_warning(self, monkeypatch):
        monkeypatch.setattr("seriousdb.logging_config.LOG_LEVEL", "WARNING")
        configure_logging()
        assert logging.getLogger().level == logging.WARNING

    def test_format_contains_expected_fields(self, monkeypatch):
        monkeypatch.setattr("seriousdb.logging_config.LOG_LEVEL", "INFO")
        configure_logging()

        root = logging.getLogger()
        handler = root.handlers[-1]
        assert handler.formatter is not None
        fmt = handler.formatter._fmt
        assert fmt is not None
        for field in ("%(asctime)s", "%(levelname)s", "%(name)s", "%(message)s"):
            assert field in fmt


class TestLogLevelFromEnv:
    """LOG_LEVEL is read from config.py which reads SERIOUSDB_LOG_LEVEL."""

    def test_env_var_sets_log_level(self, monkeypatch):
        monkeypatch.setenv("SERIOUSDB_LOG_LEVEL", "ERROR")
        # Re import the config value so the env var takes effect.
        import importlib

        import seriousdb.config as cfg

        importlib.reload(cfg)
        monkeypatch.setattr("seriousdb.logging_config.LOG_LEVEL", cfg.LOG_LEVEL)

        configure_logging()
        assert logging.getLogger().level == logging.ERROR


class TestCacheLogging:
    """Verify that cache operations emit the expected log records."""

    def test_load_logs_warning_on_corrupt_db(self, tmp_path, caplog):
        db_path = tmp_path / "corrupt.sdb"
        db_path.write_bytes(b"this is not json!!!")

        cache = Cache()
        with caplog.at_level(logging.WARNING, logger="seriousdb.persistence"):
            cache.load(str(db_path))

        assert any(
            "Corrupt" in r.message and r.levelno == logging.WARNING
            for r in caplog.records
        ), f"Expected corruption warning, got: {[r.message for r in caplog.records]}"

    def test_flush_is_a_noop(self, caplog):
        cache = Cache()  # never loaded

        with caplog.at_level(logging.DEBUG, logger="seriousdb.cache"):
            cache.flush()

        assert not any(r.levelno >= logging.WARNING for r in caplog.records)

    def test_require_db_raises_when_db_is_none(self):
        cache = Cache()
        cache.filename = "missing.sdb"
        with pytest.raises(ServiceUnavailableError, match="missing.sdb"):
            require_db(cache)

    def test_require_db_returns_db_when_loaded(self):
        cache = Cache()
        cache.db = {"a": "b"}
        assert require_db(cache) is cache.db
