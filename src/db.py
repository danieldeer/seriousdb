import os
import pickle
import threading

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


# Load the database once into memory at startup
db = load_db()
