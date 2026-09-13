# Persistence

Data is stored in a local file named `.sdb` in the process working directory.

The file contains a serialized Python dictionary written with the standard-library `json` module. On first startup, the application creates it with:

```python
{"default": "default"}
```

Each `PUT` loads the complete dictionary, changes one key, and writes the complete dictionary back to disk.

## Current constraints

- The file is local to the machine running the server.
- Requests use the complete dictionary rather than a database engine.
- Concurrent writes and multi-process access are not currently coordinated.
