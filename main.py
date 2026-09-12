import os
import pickle
import threading

from fastapi import FastAPI, HTTPException

db_file = ".sdb"
db_lock = threading.Lock()

DEFAULT_DB = {"default": "default"}


def load_db():
    try:
        with open(db_file, "rb") as f:
            return pickle.load(f)

    except (EOFError, pickle.UnpicklingError, FileNotFoundError):
        db = dict(DEFAULT_DB)
        save_db(db)
        return db


def save_db(db):
    with open(db_file, "wb") as f:
        pickle.dump(db, f)


if not os.path.isfile(db_file):
    save_db(dict(DEFAULT_DB))

app = FastAPI()


@app.put("/db")
async def put(key: str, value: str):
    with db_lock:
        db = load_db()
        db[key] = value
        save_db(db)

    return value


@app.get("/db")
async def get(key: str):
    with db_lock:
        db = load_db()

    val = db.get(key, None)

    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")

    return val
