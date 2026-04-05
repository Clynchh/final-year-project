import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

_CURRENT = Path(__file__).resolve()


def summarise_sentiment(input_csv: Path, output_csv: Path) -> None:
    monthly_data: dict = defaultdict(lambda: {"scores": [], "labels": []})

    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["source"], row["period"], row["year_month"])  # group so results stay separated per source/period
            monthly_data[key]["scores"].append(int(row["sentiment_score"]))
            monthly_data[key]["labels"].append(row["sentiment_label"])

    monthly_results = []
    for (source, period, year_month), data in sorted(monthly_data.items()):
        scores = data["scores"]
        labels = data["labels"]
        total = len(labels)

        monthly_results.append({
            "source": source,
            "period": period,
            "year_month": year_month,
            "mean_sentiment": round(mean(scores), 4),
            "median_sentiment": median(scores),
            "positive_pct": round(labels.count("positive") / total * 100, 2),
            "neutral_pct": round(labels.count("neutral") / total * 100, 2),
            "negative_pct": round(labels.count("negative") / total * 100, 2),
            "sentence_count": total,
            "sentiment_std": round(stdev(scores), 4) if len(scores) > 1 else 0.0,
        })

    fieldnames = [
        "source", "period", "year_month", "mean_sentiment", "median_sentiment",
        "positive_pct", "neutral_pct", "negative_pct", "sentence_count", "sentiment_std",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(monthly_results)

    print(f"Monthly summary saved to: {output_csv}")


if __name__ == "__main__":
    summarise_sentiment(
        _CURRENT.parent / "sentiment_analysis_details_tight_altmodel.csv",
        _CURRENT.parent / "sentiment_analysis_monthly_tight_altmodel.csv",
    )
