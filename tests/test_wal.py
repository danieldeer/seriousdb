"""Tests for WriteAheadLog: appending, replaying, and clearing entries."""

import json

import pytest

from seriousdb.wal import DeleteEntry, SetEntry, WriteAheadLog


@pytest.fixture
def wal_path(tmp_path):
    return tmp_path / "test.wal"


@pytest.fixture
def wal(wal_path):
    return WriteAheadLog(str(wal_path))


def test_replay_on_missing_file_returns_empty_list(wal):
    assert wal.replay() == []


def test_append_then_replay_returns_entries_in_order(wal):
    wal.append(SetEntry(key="a", value="1"))
    wal.append(SetEntry(key="b", value="2"))
    wal.append(DeleteEntry(key="a"))

    assert wal.replay() == [
        SetEntry(key="a", value="1"),
        SetEntry(key="b", value="2"),
        DeleteEntry(key="a"),
    ]


def test_append_writes_one_json_line_per_entry(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))

    with open(wal_path, "rb") as f:
        content = f.read()

    assert (
        content == json.dumps(SetEntry(key="a", value="1").to_dict()).encode() + b"\n"
    )


def test_replay_drops_and_truncates_a_torn_last_entry(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))
    wal.append(SetEntry(key="b", value="2"))

    with open(wal_path, "rb") as f:
        wal_bytes = f.read()
    with open(wal_path, "wb") as f:
        f.write(wal_bytes[:-3])

    entries = wal.replay()

    assert entries == [SetEntry(key="a", value="1")]

    with open(wal_path, "rb") as f:
        repaired = f.read()
    assert (
        repaired == json.dumps(SetEntry(key="a", value="1").to_dict()).encode() + b"\n"
    )


@pytest.mark.parametrize(
    "malformed",
    [
        b'{"op": "set", "key": "b"}\n',  # Missing required field
        b"[]\n",  # Unexpected top-level type
    ],
)
def test_replay_recovers_from_malformed_entry(wal, wal_path, malformed):
    wal.append(SetEntry(key="a", value="1"))

    with open(wal_path, "ab") as f:
        f.write(malformed)

    assert wal.replay() == [SetEntry(key="a", value="1")]

    with open(wal_path, "rb") as f:
        assert f.read() == (
            json.dumps(SetEntry(key="a", value="1").to_dict()).encode() + b"\n"
        )

    wal.append(SetEntry(key="c", value="3"))

    assert wal.replay() == [
        SetEntry(key="a", value="1"),
        SetEntry(key="c", value="3"),
    ]


def test_append_after_repaired_truncation_stays_valid(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))
    wal.append(SetEntry(key="b", value="2"))

    with open(wal_path, "rb") as f:
        wal_bytes = f.read()
    with open(wal_path, "wb") as f:
        f.write(wal_bytes[:-3])

    wal.replay()
    wal.append(SetEntry(key="c", value="3"))

    assert wal.replay() == [
        SetEntry(key="a", value="1"),
        SetEntry(key="c", value="3"),
    ]


def test_clear_empties_the_file(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))

    wal.clear()

    with open(wal_path, "rb") as f:
        assert f.read() == b""
    assert wal.replay() == []


def test_clear_on_nonexistent_file_creates_empty_file(tmp_path):
    wal_path = tmp_path / "fresh.wal"
    wal = WriteAheadLog(str(wal_path))

    wal.clear()

    assert wal_path.exists()
    assert wal.replay() == []


def test_append_repairs_leftover_bytes_from_a_previous_failed_write(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))

    # Simulate a write that raised before finishing
    with open(wal_path, "ab") as f:
        f.write(b'{"op": "set", "key": "b')

    wal.append(SetEntry(key="c", value="3"))

    assert wal.replay() == [
        SetEntry(key="a", value="1"),
        SetEntry(key="c", value="3"),
    ]
def test_loading_wal_with_duplicate_keys_raises_error(wal, wal_path):
    wal.append(SetEntry(key="a", value="1"))

    with open(wal_path, "a", encoding="utf-8") as f:
        f.write('{"op": "set", "key": "a", "key": "b", "value": "2"}\n')

    with pytest.raises(ValueError, match="Duplicate occurred in sdbwf: 'key'"):
        wal.replay()