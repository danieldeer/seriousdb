# seriousdb - An HTTP-based Key-Value Store

`seriousdb` is a small HTTP-based key-value store written in Python using [FastAPI](https://fastapi.tiangolo.com/).

## Requirements

- Python 3.11 or newer
- Linux (only actively supported platform for now)

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/danieldeer/seriousdb.git
cd seriousdb
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
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

If the requested key does not exist, the API returns a `404` response.
