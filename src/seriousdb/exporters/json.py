import json
from pathlib import Path


def export(
    db: dict[str, str],
    filename: str | Path,
) -> None:
    filename = Path(filename)

    with filename.open("w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write("\n")
