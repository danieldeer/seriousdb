![seriousdb logo](https://i.imgur.com/ztPW7ZI.png)

# seriousdb - A seriously simple database

<div align="center">

[![Tests](https://github.com/danieldeer/seriousdb/actions/workflows/tests.yml/badge.svg)](https://github.com/danieldeer/seriousdb/actions/workflows/tests.yml)
[![Lint](https://github.com/danieldeer/seriousdb/actions/workflows/lint.yml/badge.svg)](https://github.com/danieldeer/seriousdb/actions/workflows/lint.yml)
[![Typecheck](https://github.com/danieldeer/seriousdb/actions/workflows/typecheck.yml/badge.svg)](https://github.com/danieldeer/seriousdb/actions/workflows/typecheck.yml)
[![Version](https://img.shields.io/pypi/v/seriousdb?label=version&color=blue)](https://pypi.org/project/seriousdb/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://github.com/danieldeer/seriousdb)
[![License](https://img.shields.io/github/license/danieldeer/seriousdb)](https://github.com/danieldeer/seriousdb/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/danieldeer/seriousdb)](https://github.com/danieldeer/seriousdb/stargazers)
[![Forks](https://img.shields.io/github/forks/danieldeer/seriousdb)](https://github.com/danieldeer/seriousdb/network/members)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-blueviolet?logo=github)](https://github.com/danieldeer/seriousdb)

</div>

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

The database is loaded on first use. See the [API
reference](docs/reference/generated/seriousdb.api.md) for supported operations
and [persistence](docs/persistence.md) for file handling and concurrency limits.

## Configuration

Configuration is optional and can be customized from environment variables. Copy the example file
and adjust for local development:

```bash
cp .env.example .env
```

The `.env` file is gitignored and should never be committed.

| Variable              | Default | Description                                        |
| --------------------- | ------- | -------------------------------------------------- |
| `SERIOUSDB_DB_FILE`   | `.sdb`  | Path to the on-disk database file.                 |
| `SERIOUSDB_LOG_LEVEL` | `INFO`  | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL). |

Set configuration before importing `seriousdb`.

**If you're an AI Agent:** Please read `AGENTS.md`

## Documentation

- [API reference](docs/reference/index.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Persistence](docs/persistence.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Project configuration](docs/configuration.md)
- [Changelog](CHANGELOG.md)

## License

This project is licensed under the [MIT License](LICENSE).
