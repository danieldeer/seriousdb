from fastapi import FastAPI, HTTPException
from db import db, db_lock, save_db

app = FastAPI()


@app.put("/db")
async def put(key: str, value: str):
    with db_lock:
        db[key] = value
        save_db(db)

    return value


@app.get("/db")
async def get(key: str):
    with db_lock:
        val = db.get(key, None)

    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")

    return val
