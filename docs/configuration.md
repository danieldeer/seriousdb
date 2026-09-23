# Project configuration

SeriousDB works without configuration. Override defaults with environment variables. When running
from this repository, you can also copy [`.env.example`](../.env.example) to `.env` at the
repository root. When using the installed package, explicitly load your application's `.env` file
before importing `seriousdb` if needed; do not rely on automatic discovery.

## Configuring environment variables (for Users)

Set variables before importing `seriousdb`. Settings are read when the configuration module is
imported. Environment variables take precedence over `.env` values; missing settings use their
defaults.

`SERIOUSDB_DB_FILE` selects the database path used when `load()` is called without a filename.
`SERIOUSDB_LOG_LEVEL` sets the minimum level of log messages written to standard output.

See the [configuration table](../README.md#configuration) for names and defaults.

## Adding new environment variables (for Developers)

Prefix variables with `SERIOUSDB_`, read them only in [`config.py`](../src/seriousdb/config.py), and
provide a default. Add a brief description to `.env.example` and update the
[configuration table](../README.md#configuration).

```python
EXAMPLE_KEY = os.getenv("SERIOUSDB_EXAMPLE_KEY", "example default value")
```

Other modules import the setting:

```python
from .config import EXAMPLE_KEY
```
