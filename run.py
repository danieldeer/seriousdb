import uvicorn

if __name__ == "__main__":
    uvicorn.run("seriousdb.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
