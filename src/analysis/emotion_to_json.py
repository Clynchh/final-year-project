# Converts emotion_analysis_monthly.csv to emotion_data.json for the dashboard.

import csv
import json
from pathlib import Path

_CURRENT = Path(__file__).resolve()
RESULTS = _CURRENT.parent.parent / "results"

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    args = parser.parse_args()

    input_csv = RESULTS / "csv" / f"emotion_analysis_monthly_{args.filter}.csv"
    output_json = RESULTS / "json" / f"emotion_data_{args.filter}.json"

    data = []
    with open(input_csv, "r", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            entry = {
                "source": row["source"],
                "period": row["period"],
                "year_month": row["year_month"],
                "sentence_count": int(row["sentence_count"]),
            }
            for emotion in EMOTIONS:
                entry[f"{emotion}_pct"] = float(row[f"{emotion}_pct"])
            data.append(entry)

    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Converted {len(data)} rows to {output_json}")
