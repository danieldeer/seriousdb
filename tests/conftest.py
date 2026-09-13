import pytest
from fastapi.testclient import TestClient

from seriousdb import main
from seriousdb.cache import Cache


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_FILE", tmp_path / "test.sdb")
    monkeypatch.setattr(main, "cache", Cache())
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def clock(monkeypatch):
    class FakeClock:
        now = 1_000_000.0

        @classmethod
        def time(cls):
            return cls.now

    monkeypatch.setattr("seriousdb.db.time", FakeClock)
    return FakeClock
