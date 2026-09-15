import uvicorn
import os

HOST = os.getenv("APP_HOST", "127.0.0.1")
PORT = int(os.getenv("APP_PORT", "8000"))

if __name__ == "__main__":
    uvicorn.run("seriousdb.main:app", host=HOST, port=PORT, reload=True)
