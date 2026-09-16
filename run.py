import argparse

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="SeriousDB", description="Simple HTTP database"
    )
    parser.add_argument(
        "-p", "--port", default=8000, type=int, help="HTTP port to bind SeriousDB"
    )
    args = parser.parse_args()
    uvicorn.run("seriousdb.main:app", host="0.0.0.0", port=args.port, reload=True)
