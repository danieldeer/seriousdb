import pickle
import os
from fastapi import FastAPI
from fastapi import HTTPException

db_file = ".sdb"

# Check if the database file exists, if not populate it
if not os.path.isfile(db_file):
    with open(db_file, "wb") as f:
        pickle.dump({"default": "default"}, f)

app = FastAPI()


def read_sdb():
    with open(db_file, "rb") as f:
        return pickle.load(f)


def dump_sdb(db):
    with open(db_file, "wb+") as f:
        pickle.dump(db, f)


@app.put("/db")
async def put(key: str, value: str):
    db = read_sdb()
    db[key] = value
    dump_sdb(db)

    return value


@app.get("/db")
async def get(key: str):
    db = read_sdb()

    if db is None:
        raise HTTPException(
            status_code=404,
            detail=f"Database file {db_file} could not be opened and loaded",
        )

    val = db.get(key)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key},")

    return val
