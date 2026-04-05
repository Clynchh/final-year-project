import csv
import json
from pathlib import Path

_CURRENT = Path(__file__).resolve()


def convert_csv_to_json(input_csv: Path, output_json: Path) -> None:
    data = []
    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data.append({
                "source": row["source"],
                "period": row["period"],
                "year_month": row["year_month"],
                "mean_sentiment": float(row["mean_sentiment"]),
                "median_sentiment": float(row["median_sentiment"]),
                "positive_pct": float(row["positive_pct"]),
                "neutral_pct": float(row["neutral_pct"]),
                "negative_pct": float(row["negative_pct"]),
                "sentence_count": int(row["sentence_count"]),
                "sentiment_std": float(row["sentiment_std"]),
            })

    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Converted {len(data)} rows to {output_json}")


if __name__ == "__main__":
    convert_csv_to_json(
        _CURRENT.parent / "sentiment_analysis_monthly_tight_altmodel.csv",
        _CURRENT.parent / "sentiment_data_tight_altmodel.json",
    )
