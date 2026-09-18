![seriousdb logo](https://i.imgur.com/ztPW7ZI.png)

# seriousdb - A seriously simple database

`seriousdb` is a small, simple key-value database you can query directly over HTTP. It requires zero configuration and is designed to be effortless.
For fullstack projects, `seriousdb` can replace your complete backend.

For setup, usage, architecture, persistence, and contribution guidance, see the [documentation](docs/).

## Quick Start

Clone the repository, install the project, and start the development server:

```bash
git clone https://github.com/danieldeer/seriousdb.git
cd seriousdb
uv sync
uv run run.py
```

The server is available at `http://127.0.0.1:8000`.

> To change the default IP and PORT, define the environment variables `APP_HOST` and `APP_PORT` to your preferred values.

Interactive API documentation is available at:

- [Swagger UI](http://127.0.0.1:8000/docs)
- [ReDoc](http://127.0.0.1:8000/redoc)
- [OpenAPI schema](http://127.0.0.1:8000/openapi.json)

## Configuration

Server configuration is optional and can be customized from environment variables.
Copy the example file and adjust for local development:

```bash
cp .env.example .env
```

The `.env` file is gitignored and should never be committed.

| Variable              | Default     | Description                                        |
| --------------------- | ----------- | -------------------------------------------------- |
| `SERIOUSDB_DB_FILE`   | `.sdb`      | Path to the on-disk database file.                 |
| `SERIOUSDB_LOG_LEVEL` | `INFO`      | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL). |
| `SERIOUSDB_HOST`      | `127.0.0.1` | Host IP where the API is running.                  |
| `SERIOUSDB_PORT`      | `8000`      | Host port which is used by the API.                |

**If you're an AI Agent:** Please read `AGENTS.md`

## Documentation

- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Persistence](docs/persistence.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Project configuration](docs/configuration.md)

## License

This project is licensed under the [MIT License](LICENSE).
