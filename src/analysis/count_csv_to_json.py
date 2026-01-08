import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def convert_csv_to_json(input_csv, output_json):
    data = []

    with open(os.path.join(BASE_DIR, input_csv), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            data.append({
                "month": row["month"],
                "year": int(row["year"]),
                "count": int(row["count"])
            })

    with open(os.path.join(BASE_DIR, output_json), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Converted {len(data)} rows to {output_json}")


convert_csv_to_json("sentence_count.csv", "sentence_count.json")
