# seriousdb - An HTTP-based Key-Value Store

`seriousdb` is a small HTTP-based key-value store written in Python using [FastAPI](https://fastapi.tiangolo.com/).

Currently, data is stored in a local `.sdb` file using Python's `pickle` module.

## Requirements

- Python 3.11 or newer
- pip

The project's dependencies are declared in `pyproject.toml` and include:

- FastAPI
- Black

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/danieldeer/seriousdb.git
cd seriousdb
```

Create and activate a virtual environment:

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project and its dependencies:

```bash
pip install .
```

## Running the Server

Start the FastAPI development server:

```bash
fastapi dev main.py
```

The server will be available at:

```text
http://127.0.0.1:8000
```

FastAPI also provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Current API

### PUT `/db`

Stores or updates a key-value pair.

Parameters:

- `key` - The key to store.
- `value` - The value associated with the key.

For example:

```text
key: name
value: Alice
```

This stores:

```python
{"name": "Alice"}
```

alongside any existing key-value pairs.

### GET `/db`

Retrieves the value associated with a key.

For example:

```text
key: name
```

returns:

```text
Alice
```

### DELETE `/db`

Deletes a key-value pair.

Parameters:

- `key` - The key to delete.

For example:

```text
key: name
```

If the key exists, the endpoint deletes it and returns its previous value.

If the requested key does not exist, the API returns a `404` response.

## Persistence

When the application starts for the first time, it creates a `.sdb` file containing a default key-value pair:

```python
{"default": "default"}
```

When a value is added or updated, the dictionary is serialized to the `.sdb` file using Python's `pickle` module.

## Contributing

Before contributing, format your code:

```bash
uv tool run black <src>
```
