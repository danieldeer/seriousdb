from pathlib import Path


def _pg_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _pg_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def export(
    db: dict[str, str], filename: str | Path, table_name: str = "seriousdb_kv"
) -> None:
    filename = Path(filename)
    table = _pg_identifier(table_name)

    with filename.open("w", encoding="utf-8") as f:
        f.write(f"""CREATE TABLE IF NOT EXISTS {table} (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

""")

        for key, value in db.items():
            f.write(
                f"INSERT INTO {table} (key, value) "
                f"VALUES ({_pg_string(key)}, {_pg_string(value)}) "
                "ON CONFLICT (key) DO UPDATE "
                "SET value = EXCLUDED.value;\n"
            )
