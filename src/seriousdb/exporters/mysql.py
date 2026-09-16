from pathlib import Path


def _mysql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _mysql_identifier(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def export(
    db: dict[str, str], filename: str | Path, table_name: str = "seriousdb_kv"
) -> None:
    filename = Path(filename)
    table = _mysql_identifier(table_name)

    with filename.open("w", encoding="utf-8") as f:
        f.write(f"""CREATE TABLE IF NOT EXISTS {table} (
    `key` TEXT PRIMARY KEY,
    `value` TEXT NOT NULL
);

""")

        for key, value in db.items():
            f.write(
                f"INSERT INTO {table} (`key`, `value`) "
                f"VALUES ({_mysql_string(key)}, {_mysql_string(value)}) "
                "ON DUPLICATE KEY UPDATE "
                "`value` = VALUES(`value`);\n"
            )
