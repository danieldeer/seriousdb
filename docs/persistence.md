# Persistence

By default, data is stored in `.sdb` in the process working directory. Set
`SERIOUSDB_DB_FILE` before importing the package or starting the server to use a
different path; see [configuration](configuration.md).

The file contains a JSON object. Loading a missing file creates an empty database (`{}`). Reads use the in-memory dictionary without reloading changes from disk.

The [architecture guide](architecture.md#loading-and-writes) shows when each API
loads and writes its cache. Direct `Cache` mutations require an explicit `flush()`.

If a file contains invalid UTF-8, invalid JSON, or a JSON value other than an
object, loading moves it to `<filename>.corrupt-<unix timestamp>`, logs a warning,
and creates a new empty database. File access errors such as permission failures
can still prevent loading.

## Current constraints

- The full database must fit in memory, and each flush rewrites the entire file.
- A lock coordinates operations and flushes on one cache within a process.
  Sequences of operations are not transactions.
- Separate caches and processes have independent data and locks. Do not use the
  Python API and HTTP service to write the same file concurrently: their snapshots
  can overwrite each other's changes.
- Writes overwrite the file directly without atomic replacement or `fsync`.
  A crash can lose data or leave an incomplete file. A failed flush does not roll
  back the in-memory change.
