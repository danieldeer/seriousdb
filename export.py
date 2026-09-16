"""Command-line interface for exporting seriousdb databases."""

import argparse
from pathlib import Path

from seriousdb import exporters
from seriousdb.cache import Cache, require_db

DUMP_DIR = Path("dump")

EXPORTERS = {
    "postgresql": exporters.postgresql.export,
    "pg": exporters.postgresql.export,
    "mysql": exporters.mysql.export,
    "sqlite": exporters.sqlite.export,
    "json": exporters.json.export,
    "csv": exporters.csv.export,
}

SQL_EXPORTERS = {
    "postgresql",
    "pg",
    "mysql",
    "sqlite",
}


def main() -> None:
    """Parse arguments and export a seriousdb database."""
    parser = argparse.ArgumentParser(description="Export a seriousdb database.")

    parser.add_argument(
        "database",
        help="Path to the seriousdb database file.",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=EXPORTERS,
        required=True,
        help="Export format.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file. Defaults to 'dump/<database>.<format>'.",
    )

    parser.add_argument(
        "--table",
        default="seriousdb_kv",
        help="Table name for SQL exports.",
    )

    args = parser.parse_args()

    cache = Cache()
    cache.load(args.database)

    db = require_db(cache)
    exporter = EXPORTERS[args.format]

    if args.output:
        output = DUMP_DIR / f"{Path(args.output)}"
    else:
        database_name = Path(args.database).stem
        extension = "sql" if args.format in SQL_EXPORTERS else args.format
        output = DUMP_DIR / f"{database_name}.{extension}"

    output.parent.mkdir(parents=True, exist_ok=True)

    if args.format in SQL_EXPORTERS:
        exporter(db, output, table_name=args.table)
    else:
        exporter(db, output)

    print(f"Exported {len(db)} entries to {output}")


if __name__ == "__main__":
    main()
