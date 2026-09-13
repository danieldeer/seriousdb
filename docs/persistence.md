# Persistence

Data is stored in a local file named `.sdb` in the process working directory.

The file contains a serialized Python dictionary written with the standard-library `json` module. On first startup, the application creates it with:

```python
{"default": "default"}
```

Each `PUT` loads the complete dictionary, changes one key, and writes the complete dictionary back to disk.

Entries created without a TTL are stored as plain strings. Entries created with
a TTL are stored as a dictionary with a `value` and an absolute Unix timestamp
`expires_at`:

```python
{"session": {"value": "abc123", "expires_at": 1700000000.0}}
```

Expiration is lazy: expired entries are only removed when they are read via
`GET`, which returns a `404` for expired keys.

## Current constraints

- The file is local to the machine running the server.
- Requests use the complete dictionary rather than a database engine.
- Concurrent writes and multi-process access are not currently coordinated.
