from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .db_engine import Db_Engine

# First we initiate our database
db = Db_Engine()


# now we will create a bridge between the FastAPI server and our Db_Engine
# FastAPI will run everything before 'yield' and pause there.It will keep the server running and handle GET,PUT requests.
# When the server is about to shut down it will execute instructions below 'yield'
@asynccontextmanager
async def lifespan(app: FastAPI):
    # first load the database file into memory
    db.boot()

    yield

    # flush everything to disk before shutting down
    db.compact()


app = FastAPI(lifespan=lifespan)


@app.put("/db")
def put(key: str, value: str):
    db.put(key, value)
    return value


@app.get("/db")
def get(key: str):
    val = db.get(key)
    if val is None:
        raise HTTPException(status_code=404, detail=f"No value set for key {key}")
    return val
