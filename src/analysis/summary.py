# Aggregates per-sentence sentiment and emotion CSVs into monthly summary CSVs.

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

_CURRENT = Path(__file__).resolve()
RESULTS = _CURRENT.parent.parent / "results"

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


def summarise_emotions(input_csv: Path, output_csv: Path) -> None:
    monthly: dict = defaultdict(lambda: {e: 0 for e in EMOTIONS} | {"total": 0})

    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["source"], row["period"], row["year_month"])
            emotion = row["emotion"].lower()
            if emotion in monthly[key]:
                monthly[key][emotion] += 1
            monthly[key]["total"] += 1

    results = []
    for (source, period, year_month), data in sorted(monthly.items()):
        total = data["total"] or 1
        entry = {"source": source, "period": period, "year_month": year_month, "sentence_count": data["total"]}
        for e in EMOTIONS:
            entry[f"{e}_pct"] = round(data[e] / total * 100, 2)
        results.append(entry)

    fieldnames = ["source", "period", "year_month", "sentence_count"] + [f"{e}_pct" for e in EMOTIONS]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Emotion summary saved to: {output_csv}")


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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    args = parser.parse_args()
    f = args.filter

    summarise_sentiment(
        RESULTS / "csv" / f"sentiment_analysis_details_{f}_altmodel.csv",
        RESULTS / "csv" / f"sentiment_analysis_monthly_{f}_altmodel.csv",
    )
    # sample filter has no emotion analysis
    if f != "sample":
        summarise_emotions(
            RESULTS / "csv" / f"emotion_analysis_details_{f}.csv",
            RESULTS / "csv" / f"emotion_analysis_monthly_{f}.csv",
        )
