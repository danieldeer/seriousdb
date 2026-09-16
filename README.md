# seriousdb - An HTTP-based Key-Value Store

`seriousdb` is a small HTTP-based key-value store written in Python using [FastAPI](https://fastapi.tiangolo.com/).

For setup, usage, architecture, persistence, and contribution guidance, see the [documentation](docs/).

## Quick Start

Clone the repository, install the project, and start the development server:

```bash
git clone https://github.com/danieldeer/seriousdb.git
cd seriousdb
uv sync
uv run run.py
```

The server is available at `http://0.0.0.0:8000`.

Interactive API documentation is available at:

- [Swagger UI](http://0.0.0.0:8000/docs)
- [ReDoc](http://0.0.0.0:8000/redoc)
- [OpenAPI schema](http://0.0.0.0:8000/openapi.json)

## Configuration

Server configuration is read from environment variables. Copy the example
file and adjust for local development:

```bash
cp .env.example .env
```

The `.env` file is gitignored and should never be committed.

| Variable              | Default | Description                              |
|-----------------------|---------|------------------------------------------|
| `SERIOUSDB_DB_FILE`   | `.sdb`  | Path to the on-disk database file.       |
| `SERIOUSDB_LOG_LEVEL` | `INFO`  | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL). |

## Documentation

- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Persistence](docs/persistence.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)

## License

This project is licensed under the [MIT License](LICENSE).
