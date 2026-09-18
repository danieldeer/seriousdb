# Project configuration

SeriousDB works without configuration. Override defaults with environment variables
or a `.env` file copied from [`.env.example`](../.env.example).

## Configuring environment variables (for Users)

Set variables before importing `seriousdb` or starting the server; settings are
read when the configuration module is imported. Environment variables take
precedence over `.env` values; missing settings use their defaults.

`SERIOUSDB_DB_FILE` selects the database path. `SERIOUSDB_HOST` and `SERIOUSDB_PORT`
configure `run.py`; direct Uvicorn commands, including the Docker image's command,
use their own host and port arguments.

See the [configuration table](../README.md#configuration) for names and defaults.

## Adding new environment variables (for Developers)

Prefix variables with `SERIOUSDB_`, read them only in
[`config.py`](../src/seriousdb/config.py), and provide a default. Add a brief
description to `.env.example` and update the [configuration table](../README.md#configuration).

```python
EXAMPLE_KEY = os.getenv("SERIOUSDB_EXAMPLE_KEY", "example default value")
```

Other modules import the setting:

```python
from .config import EXAMPLE_KEY
```
