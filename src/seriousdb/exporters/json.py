"""JSON export support."""

import json
from pathlib import Path


def export(
    db: dict[str, str],
    filename: str | Path,
    table_name: str = "seriousdb_kv",
) -> None:
    """Export a key-value database to a JSON file."""
    filename = Path(filename)

    with filename.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write("\n")
