import os

from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("SERIOUSDB_DB_FILE", ".sdb")
LOG_LEVEL = os.getenv("SERIOUSDB_LOG_LEVEL", "INFO")
