import csv
import json
from pathlib import Path

_CURRENT = Path(__file__).resolve()


def convert_csv_to_json(input_csv: Path, output_json: Path) -> None:
    data = []
    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data.append({
                "month": row["month"],
                "year": int(row["year"]),
                "count": int(row["count"]),
            })

    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Converted {len(data)} rows to {output_json}")


if __name__ == "__main__":
    convert_csv_to_json(
        _CURRENT.parent / "sentence_count.csv",
        _CURRENT.parent / "sentence_count.json",
    )
