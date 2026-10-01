from unittest.mock import patch

import pytest

from benchmarks._support import (
	assert_entries,
	expected_state,
	load_cache,
	make_entries,
	mixed_operations,
	read_resident,
	run_operations,
	write_entries,
)


@pytest.mark.parametrize(
	("flush_every", "flush_count"), [(1, 5), (2, 3), (5, 1)]
)
def test_write_entries_persists_complete_batches_and_remainder(
	tmp_path, flush_every, flush_count
):
	database_file = tmp_path / "benchmark.json"
	cache = load_cache(str(database_file))
	entries = tuple((f"key-{i}", f"value-{i}") for i in range(5))

	with patch.object(cache, "flush", wraps=cache.flush) as flush:
		write_entries(cache, entries, flush_every)

	assert flush.call_count == flush_count
	reopened = load_cache(str(database_file))
	assert read_resident(reopened, entries) == [
		value for _, value in entries
	]


def test_write_entries_preserves_keys_outside_updated_subset(tmp_path):
	database_file = tmp_path / "benchmark.json"
	cache = load_cache(str(database_file))
	entries = (("unchanged", "original"), ("updated", "before"))
	write_entries(cache, entries, 2)

	write_entries(cache, (("updated", "after"),), 1)

	reopened = load_cache(str(database_file))
	assert reopened.select("unchanged") == "original"
	assert reopened.select("updated") == "after"


@pytest.mark.parametrize("flush_every", [0, -1])
def test_write_entries_rejects_invalid_frequency_before_modifying_cache(
	tmp_path, flush_every
):
	cache = load_cache(str(tmp_path / "benchmark.json"))
	with pytest.raises(ValueError, match="positive"):
		write_entries(cache, (("key", "value"),), flush_every)
	assert cache.db == {}


def test_mixed_workload_reads_and_updates_disjoint_keys(tmp_path):
	entries = make_entries(100, 32)
	operations = mixed_operations(entries)
	reads = [
		(key, value)
		for action, key, value in operations
		if action == "read"
	]
	writes = [
		(key, value)
		for action, key, value in operations
		if action == "write"
	]
	assert len(reads) == 90
	assert len(writes) == 10
	assert {key for key, _ in reads}.isdisjoint(key for key, _ in writes)
	assert dict(writes) == {key: value[::-1] for key, value in entries[:10]}

	cache = load_cache(str(tmp_path / "benchmark.json"))
	write_entries(cache, entries, len(entries))
	assert run_operations(cache, operations) == [
		value for _, value in reads
	]
	assert_entries(cache, expected_state(entries, operations))


def test_entry_verification_rejects_unexpected_keys(tmp_path):
	cache = load_cache(str(tmp_path / "benchmark.json"))
	entries = (("expected", "value"),)
	write_entries(cache, entries, 1)
	cache.insert("unexpected", "value")
	with pytest.raises(AssertionError):
		assert_entries(cache, entries)
