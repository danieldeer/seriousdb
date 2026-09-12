import pickle
import os
from fastapi import FastAPI
from fastapi import HTTPException

db_file = ".sdb"

# Check if the database file exists, if not populate it
if not os.path.isfile(db_file):
    with open(db_file, "wb") as f:
        pickle.dump({"default": "default"}, f)
    f.close()

app = FastAPI()


@app.put("/db")
async def put(key: str, value: str):
    db = None
    with open(db_file, "rb") as f:
        db = pickle.load(f)
        db[key] = value
    f.close()
    with open(db_file, "wb+") as f:
        pickle.dump(db, f)
    f.close()
    return value


@app.get("/db")
async def get(key: str):
    db = None
    with open(db_file, "rb") as f:
        db = pickle.load(f)
    f.close()
    if db is None:
        raise HTTPException(
            status_code=404,
            detail=f"Database file {db_file} could not be opened and loaded",
        )
    val = db.get(key, None)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val


@app.delete("/db")
async def delete(key: str):
    with open(db_file, "rb") as f:
        db = pickle.load(f)

    if key not in db:
        raise HTTPException(
            status_code=404,
            detail=f"No value set for key {key}",
        )

    deleted_value = db.pop(key)

    with open(db_file, "wb") as f:
        pickle.dump(db, f)

    return {
        "key": key,
        "deleted_value": deleted_value,
    }
