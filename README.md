![seriousdb logo](https://i.imgur.com/ztPW7ZI.png)

[![CI](https://github.com/danieldeer/seriousdb/actions/workflows/tests.yml/badge.svg)](https://github.com/danieldeer/seriousdb/actions/workflows/tests.yml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/danieldeer/seriousdb/releases)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# seriousdb - A seriously simple database

`seriousdb` is a small, simple key-value database you import directly into your Python project. It
requires zero configuration and is designed to be effortless.

For setup, usage, architecture, persistence, and contribution guidance, see the
[documentation](docs/).

## Quick Start

### Use as a Python library

Install with pip:

```bash
pip install seriousdb
```

Or add it to a uv project:

```bash
uv add seriousdb
```

Then use it directly from your Python project:

```python
import seriousdb

seriousdb.set("name", "Alice")
print(seriousdb.get("name"))
```

The database is loaded on first use. See the [API reference](docs/api.md) for supported operations
and [persistence](docs/persistence.md) for file handling and concurrency limits.

## Configuration

Configuration is optional and can be customized from environment variables. Copy the example file
and adjust for local development:

```bash
cp .env.example .env
```

The `.env` file is gitignored and should never be committed.

| Variable | Default | Description | | --------------------- | ------- |
--------------------------------------------------- | | `SERIOUSDB_DB_FILE` | `.sdb` | Path to the
on-disk database file. | | `SERIOUSDB_LOG_LEVEL` | `INFO` | Logging level
(DEBUG/INFO/WARNING/ERROR/CRITICAL). |

Set configuration before importing `seriousdb`.

## Documentation

- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Persistence](docs/persistence.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Project configuration](docs/configuration.md)
- [Changelog](CHANGELOG.md)

## License

This project is licensed under the [MIT License](LICENSE).
