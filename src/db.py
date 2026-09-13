import json
import os
import threading

db_file = ".sdb"
db_lock = threading.Lock()

DEFAULT_DB = {"default": "default"}


def load_db():
    with db_lock:
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (EOFError, json.JSONDecodeError, FileNotFoundError):
            db_data = dict(DEFAULT_DB)
            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(db_data, f, indent=4)
            return db_data


def save_db(db_data):
    with db_lock:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=4)


# Load into memory once when module is initialized
db = load_db()