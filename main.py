import pickle
import os
from fastapi import FastAPI, Depends
from fastapi import HTTPException
from database import get_db, edit_db
from extra import get_key_value, add_key_value

db_file = ".sdb"

# Check if the database file exists, if not populate it
if not os.path.isfile(db_file):
    with open(db_file, "wb") as f:
        pickle.dump({"default": "default"}, f)

app = FastAPI()


@app.put("/db")
async def put(key: str, value: str, db=Depends(edit_db)):
    add_key_value(db, {key: value})
    return value


@app.get("/db")
async def get(key: str, db=Depends(get_db)):
    data = get_key_value(key, db)

    if data is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return data[key]
