import csv
import json
from pathlib import Path

_CURRENT = Path(__file__).resolve()
RESULTS = _CURRENT.parent.parent / "results"


def convert_csv_to_json(input_csv: Path, output_json: Path) -> None:
    data = []
    with open(input_csv, "r", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            data.append({
                "source": row["source"],
                "period": row["period"],
                "year_month": row["year_month"],
                "mean_sentiment": float(row["mean_sentiment"]),
                "weighted_mean_sentiment": float(row.get("weighted_mean_sentiment") or row["mean_sentiment"]),
                "median_sentiment": float(row["median_sentiment"]),
                "positive_pct": float(row["positive_pct"]),
                "neutral_pct": float(row["neutral_pct"]),
                "negative_pct": float(row["negative_pct"]),
                "sentence_count": int(row["sentence_count"]),
                "covid_sentence_count": int(row.get("covid_sentence_count") or row["sentence_count"]),
                "sentiment_std": float(row["sentiment_std"]),
            })

    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Converted {len(data)} rows to {output_json}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    parser.add_argument("--model", choices=["altmodel", "vader"], default="altmodel")
    args = parser.parse_args()

    convert_csv_to_json(
        RESULTS / "csv" / f"sentiment_analysis_monthly_{args.filter}_{args.model}.csv",
        RESULTS / "json" / f"sentiment_data_{args.filter}_{args.model}.json",
    )
