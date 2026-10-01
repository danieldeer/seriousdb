import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest import MonkeyPatch

from seriousdb import api
from seriousdb.cache import Cache
from seriousdb.exceptions import ResourceNotFoundError


@pytest.fixture
def db_file(tmp_path: Path, monkeypatch: MonkeyPatch):
	monkeypatch.chdir(tmp_path)
	db_file = tmp_path / ".sdb"
	with open(db_file, "w") as f:
		json.dump({}, f)
	api.load(db_file)
	yield db_file
	api.cache.db = None
	api.cache.filename = None


def test_set_returns_stored_value(db_file):
	assert api.set("name", "Alice") == "Alice"


def test_get_returns_stored_value(db_file):
	api.set("name", "Alice")

	assert api.get("name") == "Alice"


def test_set_overwrites_existing_key(db_file):
	api.set("name", "Alice")

	assert api.set("name", "Bob") == "Bob"
	assert api.get("name") == "Bob"


def test_get_missing_key_raises(db_file):
	with pytest.raises(ResourceNotFoundError):
		api.get("does_not_exist")


def test_delete_returns_previous_value_and_removes_key(db_file):
	api.set("name", "Alice")

	assert api.delete("name") == "Alice"

	with pytest.raises(ResourceNotFoundError):
		api.get("name")


def test_delete_missing_key_raises(db_file):
	with pytest.raises(ResourceNotFoundError):
		api.delete("does_not_exist")


def test_exists_returns_whether_key_exists(db_file):
	api.set("name", "Alice")

	assert api.exists("name")
	assert not api.exists("does_not_exist")


def test_get_all_returns_all_key_value_pairs(db_file):
	api.set("name", "Alice")
	api.set("language", "Python")

	assert api.get_all() == {
		"name": "Alice",
		"language": "Python",
	}


def test_get_bulk_returns_existing_keys_only(db_file):
	api.set("name", "Daniel")
	api.set("language", "Python")

	assert api.get_bulk(["name", "does_not_exist", "language"]) == {
		"name": "Daniel",
		"language": "Python",
	}


def test_get_bulk_returns_empty_dict_when_no_keys_match(db_file):
	assert api.get_bulk(["does_not_exist"]) == {}


def test_count_returns_number_of_key_value_pairs(db_file):
	api.set("name", "Alice")
	api.set("language", "Python")

	assert api.count() == 2


def test_count_decreases_after_deleting_key(db_file):
	api.set("name", "Alice")

	assert api.count() == 1

	api.delete("name")

	assert api.count() == 0


def test_set_persists_value_to_database_file(db_file):
	api.set("name", "Alice")

	reloaded = Cache()
	reloaded.load(str(db_file))
	with reloaded.lock:
		assert reloaded.db is not None
		assert reloaded.db["name"] == "Alice"


def test_delete_persists_removal_to_database_file(db_file):
	api.set("name", "Alice")
	api.delete("name")

	with open(db_file) as f:
		assert json.load(f) == {}


def test_load_replaces_current_data(db_file):
	api.set("name", "Alice")

	other_file = db_file.parent / "other.sdb"
	with open(other_file, "w") as f:
		json.dump({"other": "data"}, f)

	api.load(other_file)

	assert api.get_all() == {"other": "data"}


def test_load_creates_file_if_missing(db_file):
	new_file = db_file.parent / "new.sdb"

	api.load(new_file)

	assert new_file.exists()
	assert api.get_all() == {}


def test_load_corrupt_file_starts_fresh(db_file):
	db_file.write_bytes(b"not json")

	api.load(db_file)

	assert api.get_all() == {}
	assert list(db_file.parent.glob("*.corrupt-*"))


def test_values_survive_reload(db_file):
	api.set("name", "Alice")

	api.load(db_file)

	assert api.get("name") == "Alice"


def test_functions_load_default_file_on_first_use(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	api.cache.db = None
	api.cache.filename = None

	try:
		api.set("name", "Alice")

		assert (tmp_path / ".sdb").exists()
		assert api.get("name") == "Alice"
	finally:
		api.cache.db = None
		api.cache.filename = None


def test_is_loaded_reflects_state(db_file):
	assert api.is_loaded()

	api.cache.db = None
	api.cache.filename = None

	assert not api.is_loaded()


def test_concurrent_sets(db_file):
	def set_value(number):
		return api.set(f"key_{number}", f"value_{number}")

	with ThreadPoolExecutor(max_workers=10) as executor:
		values = list(executor.map(set_value, range(10)))

	assert values == [f"value_{number}" for number in range(10)]
	assert api.count() == 10

	for number in range(10):
		assert api.get(f"key_{number}") == f"value_{number}"


def test_query_functions_delegate_to_cache_methods(db_file):
	with patch.object(
		api.cache, "exists", return_value=True
	) as mock_exists:
		assert api.exists("name") is True
		mock_exists.assert_called_once_with("name")

	with patch.object(
		api.cache, "get_all", return_value={"k": "v"}
	) as mock_get_all:
		assert api.get_all() == {"k": "v"}
		mock_get_all.assert_called_once_with()

	with patch.object(
		api.cache, "get_bulk", return_value={"k": "v"}
	) as mock_get_bulk:
		assert api.get_bulk(["k"]) == {"k": "v"}
		mock_get_bulk.assert_called_once_with(["k"])

	with patch.object(api.cache, "count", return_value=3) as mock_count:
		assert api.count() == 3
		mock_count.assert_called_once_with()


def test_query_functions_do_not_acquire_cache_lock_directly(db_file):
	with patch.object(api.cache, "lock") as mock_lock:
		with patch.object(api.cache, "exists"):
			api.exists("name")
		with patch.object(api.cache, "get_all"):
			api.get_all()
		with patch.object(api.cache, "get_bulk"):
			api.get_bulk(["name"])
		with patch.object(api.cache, "count"):
			api.count()

	mock_lock.__enter__.assert_not_called()
