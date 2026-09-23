# Persistence

By default, data is stored in `.sdb` in the process working directory. Set `SERIOUSDB_DB_FILE`
before importing the package to use a different path; see [configuration](configuration.md).

The file contains a JSON object. Loading a missing file creates an empty database (`{}`). Reads use
the in-memory dictionary without reloading changes from disk.

The [architecture guide](architecture.md#call-flow) shows when the API loads and writes its cache.
Direct `Cache` mutations require an explicit `flush()`.

If a file contains invalid UTF-8, invalid JSON, or a JSON value other than an object, loading moves
it to `<filename>.corrupt-<unix timestamp>` (appending a numeric suffix like `-1`, `-2` if that path
already exists), logs a warning, and creates a new empty database. File access errors such as
permission failures can still prevent loading.

## Current constraints

- The full database must fit in memory, and each flush rewrites the entire file.
- A lock coordinates operations and flushes on one cache within a process. Sequences of operations
  are not transactions.
- Separate `Cache` instances and separate processes have independent data and locks. Concurrent
  writes to the same file from more than one of them are not coordinated and can overwrite each
  other's changes.
- Each flush writes to a temp file in the same directory, then calls `fsync` on it and finally
  replaces the database with `os.replace`. A crash leaves either the old or the new file. A failed
  flush does not roll back the in memory change and can leave the temporary file behind.
