# Persistence

Data is stored in a local `.sdb` file, with `.sdb.wal` and a stable `.sdb.lock` file beside it.

The `.sdb` file contains a serialized Python dictionary written with the standard-library `json`
module. On first startup, the application creates it with:

```json
{}
```

The [architecture guide](architecture.md#call-flow) shows when the API loads and writes its cache.
Direct `Cache` mutations (such as `insert` and `delete`) are persisted immediately to disk via the
WAL. As a result, explicitly calling `flush()` is no longer required and acts as a no-op for
backward compatibility.

Each write takes the thread lock and the database's process lock, catches up with writes in the WAL,
and reloads the snapshot if another process replaced it. The WAL append is flushed and fsynced
before the in-memory dictionary changes or the request completes. Loading, WAL repair, and compaction use
the same process lock. Reads may remain stale until this process writes or reloads.

The `.sdb` file itself is not rewritten on every write. Instead, once a fixed number of writes have
accumulated in the WAL (see `COMPACTION_THRESHOLD` in `persistence.py`), the current in-memory state is
written atomically (via a temporary file and rename), so a process interruption during compaction leaves
either the previous snapshot with its WAL intact, or the new snapshot with an empty WAL, and never a
partially written or corrupted file.

On POSIX systems, file and parent-directory syncs also order snapshot replacement before WAL clearing
for power-loss recovery. Windows does not offer the same directory-sync guarantee through Python's
standard file APIs, so power-loss recovery there depends on the filesystem and OS.

On startup, `.sdb` is loaded first, then any entries remaining in `.sdb.wal` are replayed on top of
it, recovering writes made since the last compaction. If the WAL's last entry is incomplete (if for
example the process with interrupted mid-write), replay stops at that entry and everything recorded
before it is still recovered

## Current constraints

- The database, WAL, and lock file are local to the machine running the server.
- Requests use the complete in-memory dictionary rather than a database engine.
- Processes using the same local database path serialize writes through `.sdb.lock`. Keep that lock
  file in place while the database is in use.
