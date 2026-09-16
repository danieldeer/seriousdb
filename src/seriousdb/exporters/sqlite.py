"""SQLite export support."""

from pathlib import Path


def _sql_string(value: str) -> str:
    """Escape a string for use as a SQLite string literal."""
    return "'" + value.replace("'", "''") + "'"


def _sql_identifier(value: str) -> str:
    """Quote a SQLite identifier."""
    return '"' + value.replace('"', '""') + '"'


def export(
    db: dict[str, str], filename: str | Path, table_name: str = "seriousdb_kv"
) -> None:
    """Export a key-value database to a SQLite SQL file."""
    filename = Path(filename)
    table = _sql_identifier(table_name)

    with filename.open("w", encoding="utf-8") as f:
        f.write(f"""CREATE TABLE IF NOT EXISTS {table} (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

""")

        for key, value in db.items():
            f.write(
                f"INSERT OR REPLACE INTO {table} (key, value) "
                f"VALUES ({_sql_string(key)}, {_sql_string(value)});\n"
            )
