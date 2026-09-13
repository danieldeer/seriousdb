# seriousdb - An HTTP-based Key-Value Store

`seriousdb` is a small HTTP-based key-value store written in Python using [FastAPI](https://fastapi.tiangolo.com/).

For setup, usage, architecture, persistence, and contribution guidance, see the
[documentation](docs/).

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

## Documentation

- [API reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Persistence](docs/persistence.md)
- [Contributing](docs/contributing.md)

## License

This project is licensed under the [MIT License](LICENSE).
