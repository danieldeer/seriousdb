import csv
from pathlib import Path


def export(
    db: dict[str, str],
    filename: str | Path,
) -> None:
    filename = Path(filename)

    with filename.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerows(db.items())
