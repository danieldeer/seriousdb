"""In-memory key-value cache backed by a JSON file and a write-ahead log.

The whole database is held in memory as a ``dict``. Writes are durably
appended to a :class:`~seriousdb.wal.WriteAheadLog` before returning, and periodically
compacted into the full JSON snapshot file (see :data:`COMPACTION_THRESHOLD`).
All access to the data is guarded by a lock, so a single :class:`Cache` can
be shared between request handlers.
"""

import json
import logging
import os
import tempfile
import time
from collections.abc import Iterable
from threading import Lock

from .exceptions import ResourceNotFoundError, ServiceUnavailableError
from .wal import DeleteEntry, SetEntry, WalEntry, WriteAheadLog

logger = logging.getLogger(__name__)

DEFAULT_DB = {}
COMPACTION_THRESHOLD = 50


class Cache:
	"""Thread-safe in-memory key-value store persisted to a JSON file.

	A new cache holds no data. Call :meth:`load` before using it; until then
	every data access raises
	:class:`~seriousdb.exceptions.ServiceUnavailableError`.

	Attributes
	----------
	filename : str or None
	    Path of the database file, or ``None`` if nothing has been loaded.
	wal: WriteAheadLog or None
	    The write-ahead log backing this cache, or `None` if nothing has been loaded.
	db : dict of str to str or None
	    The stored key-value pairs, or ``None`` if nothing has been loaded.
	lock : threading.Lock
	    Lock that must be held while reading or changing `db`.
	_writes_since_compact : int
	    Counter for number of writes since last compaction.
	"""

	def __init__(self):
		self.filename: str | None = None
		self.wal: WriteAheadLog | None = None
		self.db: dict[str, str] | None = None
		self.lock = Lock()
		self._writes_since_compact: int = 0

	def insert(self, key: str, value: str) -> tuple[str, bool]:
		"""Store `value` under `key`, replacing any existing value.

		The change is appended to the write-ahead log (WAL) and must succeed there before
		it is applied in memory, so a failed write never leaves the live cache disagreeing
		with what is durable. The full database snapshot file is only rewritten periodically,
		by :meth:`_compact`.

		Parameters
		----------
		key : str
		    Key to store the value under.
		value : str
		    Value to store.

		Returns
		-------
		value : str
		    The stored value.
		is_new_key : bool
		    ``True`` if `key` did not exist before, ``False`` if an existing
		    value was replaced.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		OSError
		    If the write-ahead log cannot be written. `self.db` is left unchanged in this case.
		"""
		with self.lock:
			db = self._require_db()
			is_new_key = key not in db
			self._record_write(SetEntry(key=key, value=value))
			db[key] = value
			self._safe_maybe_compact()
		return value, is_new_key

	def select(self, key: str) -> str:
		"""Return the value stored under `key`.

		Parameters
		----------
		key : str
		    Key to look up.

		Returns
		-------
		str
		    The value stored under `key`.

		Raises
		------
		ResourceNotFoundError
		    If `key` does not exist.
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		with self.lock:
			val = self._require_db().get(key, None)
		if val is None:
			logger.debug("Key not found: %s", key)
			raise ResourceNotFoundError(
				f"No value set for key {key}"
			)
		return val

	def delete(self, key: str) -> str:
		"""Remove `key` and return the value it had.

		If `key` exists, its removal is appended to the write-ahead log (WAL) and
		must succeed there before it is applied in memory, so a failed write never
		leaves the live cache disagreeing with what is durable.


		Parameters
		----------
		key : str
		    Key to remove.

		Returns
		-------
		str
		    The value `key` had before it was removed.

		Raises
		------
		ResourceNotFoundError
		    If `key` does not exist.
		ServiceUnavailableError
		    If no database has been loaded.
		OSError
		    If the write-ahead log cannot be written. `self.db` is left unchanged in this case.
		"""
		with self.lock:
			db = self._require_db()
			val = db.get(key, None)
			if val is not None:
				self._record_write(DeleteEntry(key=key))
				db.pop(key, None)
				self._safe_maybe_compact()
		if val is None:
			logger.debug("Key not found: %s", key)
			raise ResourceNotFoundError(
				f"No value set for key {key}"
			)
		return val

	def exists(self, key: str) -> bool:
		"""Return whether `key` exists in the database.

		Parameters
		----------
		key : str
		    Key to look up.

		Returns
		-------
		bool
		    ``True`` if `key` exists, ``False`` otherwise.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		with self.lock:
			return key in self._require_db()

	def __contains__(self, key: str) -> bool:
		"""Return whether `key` exists in the database.

		Parameters
		----------
		key : str
		    Key to look up.

		Returns
		-------
		bool
		    ``True`` if `key` exists, ``False`` otherwise.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		return self.exists(key)

	def get_all(self) -> dict[str, str]:
		"""Return a snapshot of every key-value pair in the database.

		Returns
		-------
		dict of str to str
		    All stored key-value pairs.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		with self.lock:
			return self._require_db().copy()

	def get_bulk(self, keys: Iterable[str]) -> dict[str, str]:
		"""Return the values stored under multiple keys.

		Keys that do not exist are omitted from the result.

		Parameters
		----------
		keys : Iterable of str
		    Keys to look up.

		Returns
		-------
		dict of str to str
		    A key-value pair for each requested key that exists in the database.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		key_list = tuple(keys)
		with self.lock:
			db = self._require_db()
			return {key: db[key] for key in key_list if key in db}

	def count(self) -> int:
		"""Return the number of key-value pairs in the database.

		Returns
		-------
		int
		    The number of stored key-value pairs.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		with self.lock:
			return len(self._require_db())

	def __len__(self) -> int:
		"""Return the number of key-value pairs in the database.

		Returns
		-------
		int
		    The number of stored key-value pairs.

		Raises
		------
		ServiceUnavailableError
		    If no database has been loaded.
		"""
		return self.count()

	def load(self, filename: str) -> None:
		"""Load the database from `filename`, replacing the current data.

		If the file does not exist, it is created with an empty database.
		If it is not valid UTF-8 JSON or does not contain a JSON object, it is
		renamed to ``<filename>.corrupt-<unix timestamp>``. If that backup already
		exists, a numeric suffix is appended (such as ``-1``, ``-2``, etc) to avoid overwriting it.
		A warning is logged, and a new file with an empty database is created in its
		place.

		After the snapshot is loaded, any entries in the write-ahead log
		(``<filename>.wal``) are replayed on top of it, recovering writes
		that happened after the last compaction.

		Parameters
		----------
		filename : str
		    Path of the database file.

		Raises
		------
		OSError
		    If the file cannot be read, renamed or written.
		"""
		with self.lock:
			if not os.path.isfile(filename):
				logger.info(
					"Database file %s does not exist; creating a new database",
					filename,
				)
				self.db = _write_default(filename)
			else:
				try:
					with open(filename, "rb") as f:
						self.db = json.loads(
							f.read().decode()
						)
						if not isinstance(
							self.db, dict
						):
							raise TypeError(
								f"expected dict, got {type(self.db).__name__}"
							)
						logger.info(
							"Loaded database from %s",
							filename,
						)

				except (
					json.JSONDecodeError,
					UnicodeDecodeError,
					TypeError,
				) as e:
					backup = _generate_corrupt_backup_path(
						filename
					)
					os.replace(filename, backup)
					logger.warning(
						"Corrupt database file %s (%s); moved to %s and starting fresh",
						filename,
						e,
						backup,
					)
					self.db = _write_default(filename)
			self.filename = filename
			self.wal = WriteAheadLog(f"{filename}.wal")
			replayed = self.wal.replay()
			self._writes_since_compact = len(replayed)
			for entry in replayed:
				entry.apply(self._require_db())

	def flush(self) -> None:
		"""No-op, kept for backward compatibility.

		Durability is now handled per-write via the write-ahead log (see
		:attr:`wal`), so nothing needs to happen here. This method
		exists so that call keeps working without change.
		"""
		return

	# ------ Write-ahead log orchestration -----------------------------------------#

	def _record_write(self, entry: WalEntry) -> None:
		"""Append `entry` to the write-ahead log and bump the write counter.

		Must be called, and must succeed, before `entry` is applied to `self.db`,
		a failed append must never leave memory and the log disagreeing about
		what happened.

		Parameters
		----------
		entry : WalEntry
		            The entry to append.

		Raises
		------
		OSError
		    If the write-ahead log cannot be written.
		"""
		self._require_wal().append(entry)
		self._writes_since_compact += 1

	def _safe_maybe_compact(self) -> None:
		"""Compact if due, isolating a compaction failure from the caller.

		Called after a write has already been durably appended to the
		write-ahead log, so the write itself is safe regardless of whether
		compaction succeeds, a compaction failure must not make the
		write that triggered it look like it failed too.
		"""
		try:
			if self._writes_since_compact >= COMPACTION_THRESHOLD:
				self._compact()
		except OSError as e:
			logger.error(
				"Compaction failed after durable write to %s: %s",
				self.filename,
				e,
			)

	def _compact(self) -> None:
		"""Write `self.db` to `self.filename` and clear the write-ahead log.

		Both the snapshot and the emptied WAL are written atomically via a temporary
		file and `os.replace`, in that order, so a crash at any point during compaction
		leaves either the old snapshot with a non-empty WAL, or the new snapshot with an
		empty WAL, and never a lost or corrupted state. Replaying the same WAL entry twice is harmless,
		since ``set``/``delete`` are overlayable.

		Raises
		------
		OSError
		    If the temporary or final files cannot be written.
		"""
		if self.db is None or self.filename is None:
			return

		_atomic_write_json(self.filename, self.db)
		logger.info("Compacted database into %s", self.filename)

		if self.wal is not None:
			self.wal.clear()

		self._writes_since_compact = 0

	def _require_db(self) -> dict[str, str]:
		"""Validate and return the loaded data.

		The caller must hold ``lock`` while using the returned ``dict``.

		Returns
		-------
		dict of str to str
		    The loaded key-value pairs. This is the cache's own ``dict``, not a
		    copy.

		Raises
		------
		ServiceUnavailableError
		    If no database is loaded.
		"""
		if self.db is None:
			logger.error("Database unavailable: %s", self.filename)
			raise ServiceUnavailableError(
				f"Database file {self.filename} could not be opened and loaded"
			)

		return self.db

	def _require_wal(self) -> WriteAheadLog:
		"""Validate and return the write-ahead log.

		The caller must hold ``lock`` while using the returned log.

		Returns
		-------
		WriteAheadLog
		    The cache's write-ahead log.

		Raises
		------
		ServiceUnavailableError
		    If no database is loaded.
		"""
		if self.wal is None:
			logger.error(
				"Write-ahead log unavailable: %s", self.filename
			)
			raise ServiceUnavailableError(
				f"Database file {self.filename} could not be opened and loaded"
			)

		return self.wal


def _atomic_write_json(filename: str, data: dict[str, str]) -> None:
	"""Write `data` to `filename` atomically, via a temp file and `os.replace`.

	Cleans up the temporary file if `os.replace` fails, rather than
	leaving it behind in the destination directory.

	Raises
	------
	OSError
	    If the temporary or final files cannot be written.
	"""
	dir_name = os.path.dirname(filename) or "."
	with tempfile.NamedTemporaryFile(
		"wb", dir=dir_name, delete=False
	) as tmp_file:
		try:
			tmp_file.write(json.dumps(data).encode())
			tmp_file.flush()
			os.fsync(tmp_file.fileno())
		except Exception:
			os.unlink(tmp_file.name)
			raise
	try:
		os.replace(tmp_file.name, filename)
	except OSError:
		os.unlink(tmp_file.name)
		raise


def _write_default(filename: str) -> dict[str, str]:
	_atomic_write_json(filename, DEFAULT_DB)
	return dict(DEFAULT_DB)


def _generate_corrupt_backup_path(filename: str) -> str:
	"""Generate an unused backup path for a corrupt database file.

	The first backup uses ``<filename>.corrupt-<unix timestamp>``.
	If that path already exists, numeric suffixes such as ``-1``,
	``-2`` and so on are tried until an unused path is found.

	Parameters
	----------
	filename : str
	    Path of the database file.

	Returns
	-------
	str
	    Unused backup path.
	"""
	base = f"{filename}.corrupt-{int(time.time())}"
	if not os.path.lexists(base):
		return base
	counter = 1
	while os.path.lexists(f"{base}-{counter}"):
		counter += 1
	return f"{base}-{counter}"
